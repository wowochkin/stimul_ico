from django.contrib import admin

from .models import OneTimePayment, RequestCampaign


class StimulusRequestInline(admin.TabularInline):
    from stimuli.models import StimulusRequest
    model = StimulusRequest
    fk_name = 'campaign'
    extra = 0
    readonly_fields = ('employee', 'amount', 'justification', 'status_display', 'requested_by', 'created_at')
    fields = ('employee', 'amount', 'justification', 'status_display', 'requested_by', 'created_at')
    
    def status_display(self, obj):
        return obj.get_display_status()
    status_display.short_description = 'Статус'


@admin.register(RequestCampaign)
class RequestCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'opens_at', 'deadline', 'auto_close_day', 'auto_close_enabled')
    list_filter = ('status', 'auto_close_enabled', 'opens_at', 'deadline')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'closed_at', 'archived_at')
    inlines = [StimulusRequestInline]


@admin.register(OneTimePayment)
class OneTimePaymentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'amount', 'payment_date', 'campaign', 'created_by')
    list_filter = ('payment_date', 'campaign')
    search_fields = ('employee__full_name', 'justification')
    autocomplete_fields = ('employee', 'campaign', 'created_by')
    readonly_fields = ('created_at', 'updated_at')
