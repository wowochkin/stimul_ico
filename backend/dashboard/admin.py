from django.contrib import admin

from .models import Setting


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'decimal_value', 'text_value', 'description', 'updated_at')
    search_fields = ('key', 'description')
