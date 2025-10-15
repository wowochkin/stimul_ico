from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class Division(models.Model):
    name = models.CharField('Название подразделения', max_length=255, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'

    def __str__(self) -> str:
        return self.name


class Position(models.Model):
    name = models.CharField('Название должности', max_length=255, unique=True)
    base_salary = models.DecimalField('Оклад', max_digits=12, decimal_places=2, default=Decimal('0'))

    class Meta:
        ordering = ['name']
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'

    def __str__(self) -> str:
        return self.name


class PositionQuota(models.Model):
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='quotas', verbose_name='Подразделение')
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='quotas', verbose_name='Должность')
    total_fte = models.DecimalField('Количество ставок', max_digits=6, decimal_places=3, default=Decimal('0'))
    occupied_fte = models.DecimalField('Занятые ставки', max_digits=6, decimal_places=3, default=Decimal('0'))
    vacant_fte = models.DecimalField('Вакантные ставки', max_digits=6, decimal_places=3, default=Decimal('0'))
    comment = models.CharField('Комментарий', max_length=255, blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        unique_together = ('division', 'position')
        verbose_name = 'Позиция штатного расписания'
        verbose_name_plural = 'Позиции штатного расписания'

    def clean(self):
        super().clean()
        total = self.total_fte or Decimal('0')
        occupied = self.occupied_fte or Decimal('0')
        vacant = self.vacant_fte or Decimal('0')
        if occupied < 0 or vacant < 0:
            raise ValidationError('Количество ставок не может быть отрицательным.')
        if occupied + vacant > total:
            raise ValidationError('Сумма занятых и вакантных ставок не может превышать общее количество.')

    def __str__(self) -> str:
        return f"{self.division} — {self.position}"


class PositionQuotaVersion(models.Model):
    quota = models.ForeignKey(PositionQuota, on_delete=models.CASCADE, related_name='versions', verbose_name='Позиция')
    effective_from = models.DateField('Действует с')
    effective_to = models.DateField('Действует по', blank=True, null=True)
    total_fte = models.DecimalField('Количество ставок', max_digits=6, decimal_places=3, default=Decimal('0'))
    occupied_fte = models.DecimalField('Занятые ставки', max_digits=6, decimal_places=3, default=Decimal('0'))
    vacant_fte = models.DecimalField('Вакантные ставки', max_digits=6, decimal_places=3, default=Decimal('0'))
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        ordering = ['-effective_from', '-created_at']
        verbose_name = 'Версия штатного расписания'
        verbose_name_plural = 'Версии штатного расписания'

    def clean(self):
        super().clean()
        total = self.total_fte or Decimal('0')
        occupied = self.occupied_fte or Decimal('0')
        vacant = self.vacant_fte or Decimal('0')
        if occupied < 0 or vacant < 0:
            raise ValidationError('Количество ставок не может быть отрицательным.')
        if occupied + vacant > total:
            raise ValidationError('Сумма занятых и вакантных ставок не может превышать общее количество.')

    def __str__(self) -> str:
        return f"{self.quota} ({self.total_fte} c {self.effective_from})"
