from decimal import Decimal

from django.db import models


class Setting(models.Model):
    key = models.CharField('Ключ', max_length=64, unique=True)
    decimal_value = models.DecimalField('Числовое значение', max_digits=14, decimal_places=2, blank=True, null=True)
    text_value = models.TextField('Текстовое значение', blank=True)
    description = models.CharField('Описание', max_length=255, blank=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Настройка'
        verbose_name_plural = 'Настройки'
        permissions = [
            ('view_dashboard', 'Может просматривать дэшборд'),
        ]

    def __str__(self) -> str:
        return self.key

    @property
    def value(self) -> Decimal | str | None:
        if self.decimal_value is not None:
            return self.decimal_value
        if self.text_value:
            return self.text_value
        return None

    @classmethod
    def get_decimal(cls, key: str, default: Decimal) -> Decimal:
        try:
            setting = cls.objects.get(key=key)
        except cls.DoesNotExist:
            return default
        return setting.decimal_value if setting.decimal_value is not None else default
