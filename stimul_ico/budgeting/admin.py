from django.contrib import admin

from .models import Budget, BudgetAllocation


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('budget_type', 'year', 'month', 'total_amount', 'reserved_amount', 'spent_amount', 'available_amount')
    list_filter = ('budget_type', 'year', 'month')
    search_fields = ('year',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(BudgetAllocation)
class BudgetAllocationAdmin(admin.ModelAdmin):
    list_display = ('budget', 'recurring_period', 'campaign', 'allocated_amount', 'reserved_amount', 'spent_amount', 'available_amount')
    list_filter = ('budget__budget_type',)
    autocomplete_fields = ('budget', 'recurring_period', 'campaign')
    readonly_fields = ('created_at', 'updated_at')
