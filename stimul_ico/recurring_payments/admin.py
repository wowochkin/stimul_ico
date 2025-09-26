from django.contrib import admin

from .models import RecurringPayment, RecurringPaymentLog, RecurringPeriod


@admin.register(RecurringPeriod)
class RecurringPeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'start_date', 'end_date', 'budget_limit', 'total_payments', 'remaining_budget')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('name',)
    ordering = ('-start_date',)


class RecurringPaymentLogInline(admin.TabularInline):
    model = RecurringPaymentLog
    extra = 0
    readonly_fields = (
        'changed_at',
        'changed_by',
        'previous_amount',
        'new_amount',
        'reason',
        'previous_description',
        'new_description',
    )
    can_delete = False


@admin.register(RecurringPayment)
class RecurringPaymentAdmin(admin.ModelAdmin):
    list_display = ('period', 'employee', 'amount', 'reason', 'is_locked', 'updated_at')
    list_filter = ('period__status', 'is_locked')
    search_fields = ('employee__full_name', 'reason', 'description')
    autocomplete_fields = ('period', 'employee')
    inlines = [RecurringPaymentLogInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(RecurringPaymentLog)
class RecurringPaymentLogAdmin(admin.ModelAdmin):
    list_display = ('payment', 'changed_at', 'changed_by', 'previous_amount', 'new_amount')
    list_filter = ('changed_at', 'changed_by')
    search_fields = ('payment__employee__full_name', 'reason')
    autocomplete_fields = ('payment', 'changed_by')
    readonly_fields = ('changed_at',)
