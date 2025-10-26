from django.contrib import admin
from django.contrib import messages
from django.db import transaction

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
    actions = ['delete_with_requests']

    def get_actions(self, request):
        """Убираем стандартное действие удаления"""
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    @admin.action(description='Удалить кампанию и связанные заявки')
    def delete_with_requests(self, request, queryset):
        """Удаляет выбранные кампании вместе со всеми связанными заявками"""
        from stimuli.models import StimulusRequest
        
        deleted_campaigns = 0
        deleted_requests = 0
        
        for campaign in queryset:
            # Удаляем все связанные заявки
            requests = StimulusRequest.objects.filter(campaign=campaign)
            count = requests.count()
            requests.delete()
            deleted_requests += count
            
            # Удаляем саму кампанию
            campaign.delete()
            deleted_campaigns += 1
        
        self.message_user(
            request,
            f'Успешно удалено кампаний: {deleted_campaigns}, заявок: {deleted_requests}',
            messages.SUCCESS
        )
    
    delete_with_requests.short_description = 'Удалить кампанию и связанные заявки'

    def delete_model(self, request, obj):
        """Переопределяем стандартное удаление, чтобы удалять и связанные заявки"""
        from stimuli.models import StimulusRequest
        
        with transaction.atomic():
            # Удаляем все связанные заявки
            requests = StimulusRequest.objects.filter(campaign=obj)
            count = requests.count()
            requests.delete()
            
            # Удаляем саму кампанию
            obj.delete()
            
            self.message_user(
                request,
                f'Кампания "{obj.name}" и {count} связанных заявок успешно удалены.',
                messages.SUCCESS
            )


@admin.register(OneTimePayment)
class OneTimePaymentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'amount', 'payment_date', 'campaign', 'created_by')
    list_filter = ('payment_date', 'campaign')
    search_fields = ('employee__full_name', 'justification')
    autocomplete_fields = ('employee', 'campaign', 'created_by')
    readonly_fields = ('created_at', 'updated_at')
