from django.contrib import admin

from .models import Division, Position, PositionQuota, PositionQuotaVersion


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_salary')
    search_fields = ('name',)


class PositionQuotaVersionInline(admin.TabularInline):
    model = PositionQuotaVersion
    extra = 0
    fields = ('effective_from', 'effective_to', 'total_fte', 'occupied_fte', 'vacant_fte', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(PositionQuota)
class PositionQuotaAdmin(admin.ModelAdmin):
    list_display = ('division', 'position', 'total_fte', 'occupied_fte', 'vacant_fte', 'updated_at')
    list_filter = ('division', 'position')
    search_fields = ('division__name', 'position__name')
    inlines = [PositionQuotaVersionInline]
