from __future__ import annotations

from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class RecurringPeriodQuerySet(models.QuerySet):
    def active(self) -> 'RecurringPeriodQuerySet':
        return self.filter(status=RecurringPeriod.Status.OPEN)

    def current_for_date(self, date) -> 'RecurringPeriodQuerySet':
        return self.filter(start_date__lte=date, end_date__gte=date)


class RecurringPeriod(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        OPEN = 'open', 'Открыт'
        CLOSED = 'closed', 'Закрыт'

    name = models.CharField('Название', max_length=255)
    status = models.CharField('Статус', max_length=16, choices=Status.choices, default=Status.DRAFT)
    start_date = models.DateField('Дата начала')
    end_date = models.DateField('Дата окончания')
    budget_limit = models.DecimalField('Лимит бюджета', max_digits=14, decimal_places=2, default=Decimal('0'))
    notes = models.TextField('Комментарий', blank=True)
    closed_at = models.DateTimeField('Дата закрытия', blank=True, null=True)

    objects = RecurringPeriodQuerySet.as_manager()

    class Meta:
        ordering = ['-start_date', '-end_date', 'name']
        verbose_name = 'Период постоянных выплат'
        verbose_name_plural = 'Периоды постоянных выплат'

    def __str__(self) -> str:
        return f"{self.name} ({self.start_date:%d.%m.%Y}–{self.end_date:%d.%m.%Y})"

    def clean(self) -> None:
        if self.end_date < self.start_date:
            raise ValidationError({'end_date': 'Дата окончания не может быть раньше даты начала.'})

    @property
    def total_payments(self) -> Decimal:
        return self.payments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')

    @property
    def remaining_budget(self) -> Decimal:
        return (self.budget_limit or Decimal('0')) - self.total_payments

    def open(self) -> None:
        if self.status != self.Status.DRAFT:
            raise ValidationError('Можно открыть только период в статусе "Черновик".')
        self.status = self.Status.OPEN
        self.save(update_fields=['status'])

    def close(self, *, closed_by=None, log_message: str | None = None) -> None:
        if self.status != self.Status.OPEN:
            raise ValidationError('Закрыть можно только открытый период.')
        with transaction.atomic():
            self.status = self.Status.CLOSED
            self.closed_at = timezone.now()
            self.save(update_fields=['status', 'closed_at'])
            payments = list(self.payments.select_for_update())
            for payment in payments:
                if payment.is_locked:
                    continue
                payment.is_locked = True
                payment.save(update_fields=['is_locked'])
                payment.log_changes(
                    changed_by=closed_by,
                    previous_amount=payment.amount,
                    new_amount=payment.amount,
                    reason=log_message or 'Период закрыт.'
                )


class RecurringPaymentQuerySet(models.QuerySet):
    def for_employee(self, employee_id: int) -> 'RecurringPaymentQuerySet':
        return self.filter(employee_id=employee_id)

    def editable(self) -> 'RecurringPaymentQuerySet':
        return self.filter(is_locked=False)


class RecurringPayment(models.Model):
    period = models.ForeignKey(
        RecurringPeriod,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Период'
    )
    employee = models.ForeignKey(
        'stimuli.Employee',
        on_delete=models.CASCADE,
        related_name='recurring_payments',
        verbose_name='Сотрудник'
    )
    amount = models.DecimalField('Сумма', max_digits=14, decimal_places=2)
    reason = models.CharField('Основание выплаты', max_length=255, blank=True, default='')
    description = models.CharField('Комментарий', max_length=255, blank=True)
    is_locked = models.BooleanField('Зафиксирована', default=False)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    objects = RecurringPaymentQuerySet.as_manager()

    class Meta:
        ordering = ['period', 'employee__full_name']
        verbose_name = 'Постоянная выплата'
        verbose_name_plural = 'Постоянные выплаты'
        constraints = [
            models.UniqueConstraint(fields=['period', 'employee'], name='unique_employee_payment_per_period'),
        ]

    def __str__(self) -> str:
        reason = self.reason or 'Без основания'
        return f"{self.employee} — {self.amount:.2f} ₽ ({reason})"

    def clean(self) -> None:
        if self.amount <= 0:
            raise ValidationError({'amount': 'Сумма должна быть положительной.'})
        if self.period.status == RecurringPeriod.Status.CLOSED:
            raise ValidationError('Нельзя добавлять выплаты в закрытый период.')

    def save(self, *args, **kwargs):
        creating = self._state.adding
        previous_amount: Optional[Decimal] = None
        previous_reason: Optional[str] = None
        previous_description: Optional[str] = None
        if not creating and self.pk:
            previous = RecurringPayment.objects.filter(pk=self.pk).values('amount', 'reason', 'description', 'is_locked').first()
            if previous:
                previous_amount = previous['amount']
                previous_reason = previous['reason']
                previous_description = previous['description']
                if previous['is_locked']:
                    self.is_locked = True
        super().save(*args, **kwargs)
        if creating:
            return
        if previous_amount is not None and previous_amount != self.amount:
            self.log_changes(
                previous_amount=previous_amount,
                new_amount=self.amount,
                reason='Сумма обновлена.',
                previous_description=previous_description,
                new_description=self.description,
            )
        if previous_reason is not None and previous_reason != self.reason:
            self.log_changes(
                previous_amount=self.amount,
                new_amount=self.amount,
                reason='Основание выплаты обновлено.',
                previous_description=previous_reason,
                new_description=self.reason,
            )
        elif previous_description is not None and previous_description != self.description:
            self.log_changes(
                previous_amount=self.amount,
                new_amount=self.amount,
                reason='Комментарий обновлён.',
                previous_description=previous_description,
                new_description=self.description,
            )

    def lock(self, *, reason: str = 'Выплата зафиксирована.', user=None) -> None:
        if self.is_locked:
            return
        self.is_locked = True
        self.save(update_fields=['is_locked'])
        self.log_changes(
            changed_by=user,
            previous_amount=self.amount,
            new_amount=self.amount,
            reason=reason,
        )

    def log_changes(
        self,
        *,
        changed_by=None,
        previous_amount: Decimal,
        new_amount: Decimal,
        reason: str,
        previous_description: str | None = None,
        new_description: str | None = None,
    ) -> 'RecurringPaymentLog':
        return RecurringPaymentLog.objects.create(
            payment=self,
            changed_by=changed_by,
            previous_amount=previous_amount,
            new_amount=new_amount,
            previous_description=previous_description or self.description,
            new_description=new_description or self.description,
            reason=reason,
        )


class RecurringPaymentLog(models.Model):
    payment = models.ForeignKey(
        RecurringPayment,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='Выплата'
    )
    changed_at = models.DateTimeField('Дата изменения', auto_now_add=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='recurring_payment_logs',
        verbose_name='Пользователь',
        null=True,
        blank=True,
    )
    previous_amount = models.DecimalField('Предыдущее значение', max_digits=14, decimal_places=2)
    new_amount = models.DecimalField('Новое значение', max_digits=14, decimal_places=2)
    previous_description = models.CharField('Описание (до)', max_length=255, blank=True)
    new_description = models.CharField('Описание (после)', max_length=255, blank=True)
    reason = models.CharField('Причина изменения', max_length=255)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Журнал изменения выплаты'
        verbose_name_plural = 'Журнал изменений выплат'

    def __str__(self) -> str:
        return f"{self.payment} — {self.changed_at:%d.%m.%Y %H:%M}"
