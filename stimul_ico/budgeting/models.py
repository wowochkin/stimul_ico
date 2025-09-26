from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction


class Budget(models.Model):
    class BudgetType(models.TextChoices):
        RECURRING = 'recurring', 'Постоянные выплаты'
        ONE_TIME = 'one_time', 'Разовые выплаты'

    year = models.PositiveIntegerField('Год')
    month = models.PositiveSmallIntegerField('Месяц', blank=True, null=True)
    budget_type = models.CharField('Тип бюджета', max_length=16, choices=BudgetType.choices)
    total_amount = models.DecimalField('Всего средств', max_digits=14, decimal_places=2)
    reserved_amount = models.DecimalField('Зарезервировано', max_digits=14, decimal_places=2, default=Decimal('0'))
    spent_amount = models.DecimalField('Израсходовано', max_digits=14, decimal_places=2, default=Decimal('0'))
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        ordering = ['-year', '-month', 'budget_type']
        verbose_name = 'Бюджет'
        verbose_name_plural = 'Бюджеты'
        unique_together = ('year', 'month', 'budget_type')

    def __str__(self) -> str:
        target = f"{self.year}"
        if self.month:
            target = f"{self.month:02}.{self.year}"
        return f"{self.get_budget_type_display()} — {target}"

    @property
    def available_amount(self) -> Decimal:
        return (self.total_amount or Decimal('0')) - (self.reserved_amount or Decimal('0')) - (self.spent_amount or Decimal('0'))

    def reserve(self, amount: Decimal, *, save: bool = True) -> None:
        if amount <= 0:
            raise ValidationError('Резервирование должно быть положительным.')
        if amount > self.available_amount:
            raise ValidationError('Недостаточно бюджета для резерва.')
        self.reserved_amount += amount
        if save:
            self.save(update_fields=['reserved_amount'])

    def spend(self, amount: Decimal, *, release_reserve: bool = True, save: bool = True) -> None:
        if amount <= 0:
            raise ValidationError('Расход должен быть положительным.')
        if release_reserve:
            if amount > self.reserved_amount:
                raise ValidationError('Недостаточно зарезервированных средств.')
            self.reserved_amount -= amount
        else:
            if amount > self.available_amount:
                raise ValidationError('Недостаточно бюджета для расхода.')
        self.spent_amount += amount
        if save:
            self.save(update_fields=['reserved_amount', 'spent_amount'])


class BudgetAllocation(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='allocations', verbose_name='Бюджет')
    recurring_period = models.ForeignKey(
        'recurring_payments.RecurringPeriod',
        on_delete=models.CASCADE,
        related_name='budget_allocations',
        verbose_name='Период постоянных выплат',
        null=True,
        blank=True,
    )
    campaign = models.ForeignKey(
        'one_time_payments.RequestCampaign',
        on_delete=models.CASCADE,
        related_name='budget_allocations',
        verbose_name='Кампания',
        null=True,
        blank=True,
    )
    allocated_amount = models.DecimalField('Выделено средств', max_digits=14, decimal_places=2)
    reserved_amount = models.DecimalField('Зарезервировано', max_digits=14, decimal_places=2, default=Decimal('0'))
    spent_amount = models.DecimalField('Израсходовано', max_digits=14, decimal_places=2, default=Decimal('0'))
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Выделение бюджета'
        verbose_name_plural = 'Выделения бюджета'
        constraints = [
            models.CheckConstraint(
                check=(
                    (models.Q(recurring_period__isnull=False) & models.Q(campaign__isnull=True)) |
                    (models.Q(recurring_period__isnull=True) & models.Q(campaign__isnull=False))
                ),
                name='allocation_single_target'
            ),
        ]

    def __str__(self) -> str:
        target = self.recurring_period or self.campaign
        return f"{self.budget} → {target}"

    def clean(self) -> None:
        if bool(self.recurring_period) == bool(self.campaign):
            raise ValidationError('Выберите либо период, либо кампанию для распределения бюджета.')
        if self.allocated_amount <= 0:
            raise ValidationError({'allocated_amount': 'Размер выделенного бюджета должен быть положительным.'})

    @property
    def available_amount(self) -> Decimal:
        return (self.allocated_amount or Decimal('0')) - (self.reserved_amount or Decimal('0')) - (self.spent_amount or Decimal('0'))

    def reserve(self, amount: Decimal, *, save: bool = True) -> None:
        if amount <= 0:
            raise ValidationError('Сумма резерва должна быть положительной.')
        if amount > self.available_amount:
            raise ValidationError('Недостаточно средств в выделении.')
        self.reserved_amount += amount
        self.budget.reserved_amount += amount
        if save:
            with transaction.atomic():
                self.budget.save(update_fields=['reserved_amount'])
                self.save(update_fields=['reserved_amount'])

    def release(self, amount: Decimal, *, save: bool = True) -> None:
        if amount <= 0:
            raise ValidationError('Сумма списания должна быть положительной.')
        if amount > self.reserved_amount:
            raise ValidationError('Недостаточно зарезервированных средств.')
        self.reserved_amount -= amount
        self.budget.reserved_amount -= amount
        if save:
            with transaction.atomic():
                self.budget.save(update_fields=['reserved_amount'])
                self.save(update_fields=['reserved_amount'])

    def spend(self, amount: Decimal, *, release_reserve: bool = True, save: bool = True) -> None:
        if amount <= 0:
            raise ValidationError('Сумма должна быть положительной.')
        if release_reserve:
            if amount > self.reserved_amount:
                raise ValidationError('Недостаточно зарезервированных средств.')
            self.reserved_amount -= amount
            self.budget.reserved_amount -= amount
        else:
            if amount > self.available_amount:
                raise ValidationError('Недостаточно средств в выделении.')
            if amount > self.budget.available_amount:
                raise ValidationError('Недостаточно средств в бюджете.')
        self.spent_amount += amount
        self.budget.spent_amount += amount
        if save:
            with transaction.atomic():
                self.budget.save(update_fields=['reserved_amount', 'spent_amount'])
                self.save(update_fields=['reserved_amount', 'spent_amount'])
