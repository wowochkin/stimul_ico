from django.contrib import admin

from .models import OneTimePayment, RequestCampaign


@admin.register(RequestCampaign)
class RequestCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'opens_at', 'deadline', 'auto_close_day', 'auto_close_enabled')
    list_filter = ('status', 'auto_close_enabled', 'opens_at', 'deadline')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'closed_at', 'archived_at')


@admin.register(OneTimePayment)
class OneTimePaymentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'amount', 'payment_date', 'campaign', 'created_by')
    list_filter = ('payment_date', 'campaign')
    search_fields = ('employee__full_name', 'justification')
    autocomplete_fields = ('employee', 'campaign', 'created_by')
    readonly_fields = ('created_at', 'updated_at')
