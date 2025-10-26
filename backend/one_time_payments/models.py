from __future__ import annotations

from datetime import date
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class RequestCampaignQuerySet(models.QuerySet):
    def active(self) -> 'RequestCampaignQuerySet':
        today = timezone.localdate()
        return self.filter(status=RequestCampaign.Status.OPEN, opens_at__lte=today).filter(
            models.Q(deadline__isnull=True) | models.Q(deadline__gte=today)
        )


class RequestCampaign(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        OPEN = 'open', 'Открыта'
        CLOSED = 'closed', 'Закрыта'
        ARCHIVED = 'archived', 'В архиве'

    name = models.CharField('Название кампании', max_length=255)
    description = models.TextField('Описание', blank=True)
    status = models.CharField('Статус', max_length=16, choices=Status.choices, default=Status.DRAFT)
    opens_at = models.DateField('Дата открытия')
    deadline = models.DateField('Дедлайн', blank=True, null=True)
    auto_close_day = models.PositiveSmallIntegerField(
        'Дата автозакрытия',
        default=15,
        help_text='Если дедлайн не указан, кампания автоматически закрывается в указанный день месяца.'
    )
    auto_close_enabled = models.BooleanField('Автоматическое закрытие', default=True)
    closed_at = models.DateTimeField('Закрыта', blank=True, null=True)
    archived_at = models.DateTimeField('В архиве с', blank=True, null=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    objects = RequestCampaignQuerySet.as_manager()

    class Meta:
        ordering = ['-opens_at', 'name']
        verbose_name = 'Кампания заявок'
        verbose_name_plural = 'Кампании заявок'

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        if self.deadline and self.deadline < self.opens_at:
            raise ValidationError({'deadline': 'Дедлайн не может быть раньше даты открытия.'})

    def should_auto_close(self, on_date: Optional[date] = None) -> bool:
        if not self.auto_close_enabled or self.status != self.Status.OPEN:
            return False
        on_date = on_date or timezone.localdate()
        if self.deadline:
            return on_date > self.deadline
        # Автозакрытие по дню месяца
        return on_date.day > self.auto_close_day

    def open(self) -> None:
        if self.status != self.Status.DRAFT:
            raise ValidationError('Открыть можно только кампания из черновика.')
        self.status = self.Status.OPEN
        self.save(update_fields=['status'])

    def close(self, *, archive: bool = True, closed_by=None) -> None:
        if self.status != self.Status.OPEN:
            raise ValidationError('Закрыть можно только открытую кампанию.')
        self.status = self.Status.CLOSED
        self.closed_at = timezone.now()
        self.save(update_fields=['status', 'closed_at'])
        if archive:
            self.archive()

    def reopen(self) -> None:
        """Переоткрывает закрытую кампанию"""
        if self.status != self.Status.CLOSED:
            raise ValidationError('Переоткрыть можно только закрытую кампанию.')
        self.status = self.Status.OPEN
        self.closed_at = None
        self.save(update_fields=['status', 'closed_at'])

    def archive(self) -> None:
        """Архивирует кампанию и все связанные заявки"""
        if self.status not in (self.Status.CLOSED, self.Status.ARCHIVED):
            raise ValidationError('В архив можно отправить только закрытую кампанию.')
        
        with transaction.atomic():
            from stimuli.models import StimulusRequest  # локальный импорт во избежание циклов
            base_qs = StimulusRequest.objects.filter(campaign=self)
            
            # Проверяем, что все заявки рассмотрены (одобрены или отклонены)
            pending_requests = base_qs.filter(status=StimulusRequest.Status.PENDING)
            if pending_requests.exists():
                raise ValidationError(
                    f'Нельзя архивировать кампанию: есть нерассмотренные заявки '
                    f'({pending_requests.count()} шт.). Все заявки должны быть одобрены или отклонены.'
                )
            
            # Сохраняем итоговый статус для каждой заявки при архивировании
            for request in base_qs:
                final_status = f"{request.get_status_display()} (Архив)"
                request.final_status = final_status
                request.status = StimulusRequest.Status.ARCHIVED
                request.archived_at = timezone.now()
                request.save(update_fields=['final_status', 'status', 'archived_at'])
            
            # Архивируем саму кампанию
            self.status = self.Status.ARCHIVED
            self.archived_at = timezone.now()
            self.save(update_fields=['status', 'archived_at'])


class OneTimePayment(models.Model):
    employee = models.ForeignKey(
        'stimuli.Employee',
        on_delete=models.CASCADE,
        related_name='one_time_payments',
        verbose_name='Сотрудник'
    )
    amount = models.DecimalField('Сумма', max_digits=14, decimal_places=2)
    payment_date = models.DateField('Дата выплаты', default=timezone.localdate)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='one_time_payments',
        verbose_name='Создано пользователем',
        null=True,
        blank=True,
    )
    campaign = models.ForeignKey(
        RequestCampaign,
        on_delete=models.SET_NULL,
        related_name='manual_payments',
        verbose_name='Кампания',
        null=True,
        blank=True,
    )
    justification = models.TextField('Обоснование', blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']
        verbose_name = 'Разовая выплата'
        verbose_name_plural = 'Разовые выплаты'

    def __str__(self) -> str:
        return f"{self.employee} — {self.amount:.2f} ₽"

    def clean(self) -> None:
        if self.amount <= 0:
            raise ValidationError({'amount': 'Сумма должна быть положительной.'})
        if self.campaign and self.campaign.status == RequestCampaign.Status.DRAFT:
            raise ValidationError({'campaign': 'Нельзя привязать выплату к кампании в черновике.'})
