from django.contrib import admin

from .models import Employee, InternalAssignment, StimulusRequest, UserDivision


class InternalAssignmentInline(admin.TabularInline):
    model = InternalAssignment
    extra = 1
    autocomplete_fields = ('position',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'user',
        'division',
        'position',
        'category',
        'rate',
        'salary_display',
        'allowance_amount_display',
        'payment',
    )
    list_filter = ('category', 'division', 'position')
    search_fields = ('full_name', 'user__username', 'division__name', 'position__name')
    autocomplete_fields = ('user', 'division', 'position')
    inlines = [InternalAssignmentInline]

    @admin.display(description='Расчётный оклад')
    def salary_display(self, obj):
        return obj.salary_amount

    @admin.display(description='Надбавка')
    def allowance_amount_display(self, obj):
        return obj.allowance_total


@admin.register(InternalAssignment)
class InternalAssignmentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'position', 'rate', 'allowance_amount', 'allowance_until')
    search_fields = ('employee__full_name', 'position__name')
    list_filter = ('position',)
    autocomplete_fields = ('employee', 'position')


@admin.register(StimulusRequest)
class StimulusRequestAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'campaign',
        'amount',
        'status_display',
        'requested_by',
        'created_at',
        'archived_at',
    )
    list_filter = ('status', 'campaign', 'created_at')
    search_fields = ('employee__full_name', 'requested_by__username', 'campaign__name')
    autocomplete_fields = ('employee', 'requested_by', 'campaign')
    readonly_fields = ('created_at', 'updated_at', 'archived_at')

    @admin.display(description='Статус')
    def status_display(self, obj):
        return obj.get_display_status()


@admin.register(UserDivision)
class UserDivisionAdmin(admin.ModelAdmin):
    list_display = ('user', 'division')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'division__name')
    autocomplete_fields = ('user', 'division')
