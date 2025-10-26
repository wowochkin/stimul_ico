from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Employee(models.Model):
    class Category(models.TextChoices):
        AUP = 'АУП', _('Административно-управленческий персонал')
        PPS = 'ППС', _('Профессорско-преподавательский состав')
        OTHER = 'Другое', _('Другое')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='employee_profile',
        verbose_name='Пользователь',
        blank=True,
        null=True
    )
    full_name = models.CharField('ФИО', max_length=255)
    division = models.ForeignKey('staffing.Division', on_delete=models.PROTECT, related_name='employees', verbose_name='Подразделение')
    position = models.ForeignKey('staffing.Position', on_delete=models.PROTECT, related_name='employees', verbose_name='Должность')
    category = models.CharField('Категория', max_length=32, choices=Category.choices)
    rate = models.DecimalField('Ставка', max_digits=6, decimal_places=3, default=1)
    allowance_amount = models.DecimalField('Надбавка', max_digits=12, decimal_places=2, default=0)
    allowance_reason = models.CharField('Основание надбавки', max_length=255, blank=True)
    allowance_until = models.DateField('Срок надбавки', blank=True, null=True)
    payment = models.DecimalField('Выплата', max_digits=12, decimal_places=2, default=0)
    justification = models.TextField('Обоснование', blank=True)

    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'

    def __str__(self):
        return self.full_name

    @property
    def salary_amount(self):
        base = self.position.base_salary if self.position else Decimal('0')
        rate = self.rate or Decimal('0')
        return base * rate

    @property
    def assignments_salary_amount(self):
        total = Decimal('0')
        for assignment in self.assignments.select_related('position').all():
            base = assignment.position.base_salary if assignment.position else Decimal('0')
            rate = assignment.rate or Decimal('0')
            total += base * rate
        return total

    @property
    def total_salary_amount(self):
        return self.salary_amount + self.assignments_salary_amount

    @property
    def allowance_total(self):
        total = self.allowance_amount or Decimal('0')
        for assignment in self.assignments.all():
            total += assignment.allowance_amount or Decimal('0')
        return total

    @property
    def total_payments(self):
        payment = self.payment or Decimal('0')
        return self.total_salary_amount + self.allowance_total + payment


class InternalAssignment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='assignments', verbose_name='Сотрудник')
    position = models.ForeignKey('staffing.Position', on_delete=models.PROTECT, related_name='assignments', verbose_name='Должность')
    rate = models.DecimalField('Ставка', max_digits=6, decimal_places=3, default=1)
    allowance_amount = models.DecimalField('Надбавка', max_digits=12, decimal_places=2, default=0)
    allowance_reason = models.CharField('Основание надбавки', max_length=255, blank=True)
    allowance_until = models.DateField('Срок надбавки', blank=True, null=True)

    class Meta:
        verbose_name = 'Внутреннее совмещение'
        verbose_name_plural = 'Внутренние совмещения'

    def __str__(self):
        return f"{self.employee} — {self.position} ({self.rate})"


class StimulusRequestQuerySet(models.QuerySet):
    def active(self):
        return self.exclude(status=self.model.Status.ARCHIVED)

    def archived(self):
        return self.filter(status=self.model.Status.ARCHIVED)

    def for_campaign(self, campaign_id):
        return self.filter(campaign_id=campaign_id)


class StimulusRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('На рассмотрении')
        APPROVED = 'approved', _('Одобрено')
        REJECTED = 'rejected', _('Отклонено')
        ARCHIVED = 'archived', _('Архив')

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='requests', verbose_name='Сотрудник')
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stimulus_requests',
        verbose_name='Ответственный'
    )
    campaign = models.ForeignKey(
        'one_time_payments.RequestCampaign',
        on_delete=models.PROTECT,
        related_name='stimulus_requests',
        verbose_name='Кампания',
    )
    amount = models.DecimalField('Размер выплаты', max_digits=12, decimal_places=2)
    justification = models.TextField('Обоснование')
    status = models.CharField('Статус', max_length=16, choices=Status.choices, default=Status.PENDING)
    final_status = models.CharField('Итоговый статус', max_length=32, blank=True, help_text='Статус на момент архивирования кампании')
    admin_comment = models.TextField('Комментарий администратора', blank=True)
    archived_at = models.DateTimeField('В архиве с', blank=True, null=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    objects = StimulusRequestQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('view_all_requests', 'Может видеть все заявки'),
            ('edit_pending_requests', 'Может редактировать заявки на рассмотрении'),
        ]
        verbose_name = 'Заявка на стимулирование'
        verbose_name_plural = 'Заявки на стимулирование'

    def get_display_status(self):
        """Возвращает отображаемый статус заявки"""
        if self.final_status:
            return self.final_status
        return self.get_status_display()

    def __str__(self):
        campaign = f' · {self.campaign}' if self.campaign else ''
        return f"{self.employee} — {self.amount} ({self.get_display_status()}){campaign}"

    def save(self, *args, **kwargs):
        if self.status != self.Status.ARCHIVED and self.archived_at:
            self.archived_at = None
        super().save(*args, **kwargs)

    def archive(self, *, save: bool = True) -> None:
        if self.status == self.Status.ARCHIVED:
            return
        self.status = self.Status.ARCHIVED
        self.archived_at = timezone.now()
        if save:
            self.save(update_fields=['status', 'archived_at'])

    @property
    def is_archived(self) -> bool:
        return self.status == self.Status.ARCHIVED


class UserDivision(models.Model):
    """Связь пользователя с подразделением для определения прав доступа"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_division',
        verbose_name='Пользователь'
    )
    division = models.ForeignKey(
        'staffing.Division',
        on_delete=models.CASCADE,
        related_name='managers',
        verbose_name='Подразделение',
        null=True,
        blank=True,
        help_text='Оставьте пустым для доступа ко всем сотрудникам'
    )
    can_view_all = models.BooleanField(
        'Доступ ко всем сотрудникам',
        default=False,
        help_text='Если включено, пользователь видит всех сотрудников независимо от подразделения'
    )

    class Meta:
        verbose_name = 'Подразделение пользователя'
        verbose_name_plural = 'Подразделения пользователей'

    def __str__(self):
        if self.can_view_all:
            return f"{self.user.username} — Все сотрудники"
        if self.division:
            return f"{self.user.username} — {self.division.name}"
        return f"{self.user.username} — без подразделения"
