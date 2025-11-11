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

    def current(self) -> Optional['RequestCampaign']:
        """
        Возвращает текущую активную кампанию, если она доступна.
        Кампания считается текущей, когда она открыта, дата открытия наступила,
        а дедлайн ещё не прошёл (или отсутствует).
        """
        return self.active().order_by('-opens_at', 'name').first()


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
        'Дата автозакрытия (устарело)',
        default=15,
        help_text='Устаревшее поле, будет удалено.',
        null=True,
        blank=True,
    )
    auto_close_enabled = models.BooleanField(
        'Автоматическое закрытие', 
        default=True,
        help_text='Кампания автоматически закроется в 00:00 дня после дедлайна.'
    )
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
        """
        Проверяет, должна ли кампания автоматически закрыться.
        Кампания закрывается в 00:00 дня после дедлайна.
        Например, если дедлайн 07.11.2025, то закрытие произойдет 08.11.2025 в 00:00.
        """
        if not self.auto_close_enabled or self.status != self.Status.OPEN:
            return False
        if not self.deadline:
            return False
        on_date = on_date or timezone.localdate()
        # Закрываем, если текущая дата больше дедлайна (наступил следующий день)
        return on_date > self.deadline

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

    def get_requested_amounts_summary(self) -> dict:
        """
        Возвращает сводку по запрошенным средствам в разрезе статусов.
        """
        from decimal import Decimal
        from django.db.models import Sum, Q
        from stimuli.models import StimulusRequest
        
        base_qs = StimulusRequest.objects.filter(campaign=self)
        
        # Подсчитываем суммы по каждому статусу
        pending_sum = base_qs.filter(status=StimulusRequest.Status.PENDING).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        # Для одобренных: включаем и текущие approved, и архивированные с пометкой "Одобрено"
        approved_sum = base_qs.filter(
            Q(status=StimulusRequest.Status.APPROVED) |
            Q(status=StimulusRequest.Status.ARCHIVED, final_status__icontains='Одобрено')
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Для отклоненных: включаем и текущие rejected, и архивированные с пометкой "Отклонено"
        rejected_sum = base_qs.filter(
            Q(status=StimulusRequest.Status.REJECTED) |
            Q(status=StimulusRequest.Status.ARCHIVED, final_status__icontains='Отклонено')
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Общая сумма всех заявок
        total_sum = base_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Считаем количество заявок по статусам
        pending_count = base_qs.filter(status=StimulusRequest.Status.PENDING).count()
        approved_count = base_qs.filter(
            Q(status=StimulusRequest.Status.APPROVED) |
            Q(status=StimulusRequest.Status.ARCHIVED, final_status__icontains='Одобрено')
        ).count()
        rejected_count = base_qs.filter(
            Q(status=StimulusRequest.Status.REJECTED) |
            Q(status=StimulusRequest.Status.ARCHIVED, final_status__icontains='Отклонено')
        ).count()
        total_count = base_qs.count()
        
        return {
            'pending': {'amount': pending_sum, 'count': pending_count},
            'approved': {'amount': approved_sum, 'count': approved_count},
            'rejected': {'amount': rejected_sum, 'count': rejected_count},
            'total': {'amount': total_sum, 'count': total_count},
        }


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
