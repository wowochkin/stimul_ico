from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from django.db.models import Sum
from django.db.models.functions import TruncMonth

from budgeting.models import BudgetAllocation
from one_time_payments.models import OneTimePayment
from recurring_payments.models import RecurringPayment
from stimuli.models import Employee, StimulusRequest

from .models import Setting


@dataclass
class DashboardFilters:
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    division_id: Optional[int] = None
    employee_id: Optional[int] = None


def _as_decimal(value) -> Decimal:
    if value is None:
        return Decimal('0')
    if isinstance(value, Decimal):
        return value
    return Decimal(value)


def _apply_employee_filters(qs, filters: DashboardFilters):
    if filters.division_id:
        qs = qs.filter(division_id=filters.division_id)
    if filters.employee_id:
        qs = qs.filter(pk=filters.employee_id)
    return qs


def _apply_payment_filters(qs, filters: DashboardFilters, date_field: str):
    if filters.start_date:
        qs = qs.filter(**{f'{date_field}__gte': filters.start_date})
    if filters.end_date:
        qs = qs.filter(**{f'{date_field}__lte': filters.end_date})
    return qs


def _normalize_month(value):
    if value is None:
        return None
    if hasattr(value, 'date'):
        return value.date()
    return value


def collect_dashboard_metrics(filters: DashboardFilters) -> Dict[str, object]:
    employee_qs = Employee.objects.select_related('division', 'position').prefetch_related('assignments__position')
    employee_qs = _apply_employee_filters(employee_qs, filters)
    employees: List[Employee] = list(employee_qs)
    employee_ids = [employee.id for employee in employees]

    recurring_qs = RecurringPayment.objects.select_related('employee__division', 'period')
    if employee_ids:
        recurring_qs = recurring_qs.filter(employee_id__in=employee_ids)
    recurring_qs = _apply_payment_filters(recurring_qs, filters, 'period__start_date')

    onetime_qs = OneTimePayment.objects.select_related('employee__division', 'campaign')
    if employee_ids:
        onetime_qs = onetime_qs.filter(employee_id__in=employee_ids)
    onetime_qs = _apply_payment_filters(onetime_qs, filters, 'payment_date')

    requests_qs = StimulusRequest.objects.filter(status=StimulusRequest.Status.APPROVED)
    if employee_ids:
        requests_qs = requests_qs.filter(employee_id__in=employee_ids)
    requests_qs = _apply_payment_filters(requests_qs, filters, 'created_at')

    monthly_totals = defaultdict(lambda: {
        'month': None,
        'recurring': Decimal('0'),
        'one_time': Decimal('0'),
        'requests': Decimal('0'),
    })

    recurring_by_month = recurring_qs.annotate(month=TruncMonth('period__start_date')).values('month').annotate(total=Sum('amount'))
    for entry in recurring_by_month:
        month = _normalize_month(entry['month'])
        bucket = monthly_totals[month]
        bucket['month'] = month
        bucket['recurring'] += _as_decimal(entry['total'])

    onetime_by_month = onetime_qs.annotate(month=TruncMonth('payment_date')).values('month').annotate(total=Sum('amount'))
    for entry in onetime_by_month:
        month = _normalize_month(entry['month'])
        bucket = monthly_totals[month]
        bucket['month'] = month
        bucket['one_time'] += _as_decimal(entry['total'])

    request_by_month = requests_qs.annotate(month=TruncMonth('created_at')).values('month').annotate(total=Sum('amount'))
    for entry in request_by_month:
        month = _normalize_month(entry['month'])
        bucket = monthly_totals[month]
        bucket['month'] = month
        bucket['requests'] += _as_decimal(entry['total'])

    monthly_totals_list = sorted(monthly_totals.values(), key=lambda item: item['month'] or date.min)

    recurring_by_employee = {
        item['employee_id']: _as_decimal(item['total'])
        for item in recurring_qs.values('employee_id').annotate(total=Sum('amount'))
    }
    onetime_by_employee = {
        item['employee_id']: _as_decimal(item['total'])
        for item in onetime_qs.values('employee_id').annotate(total=Sum('amount'))
    }
    requests_by_employee = {
        item['employee_id']: _as_decimal(item['total'])
        for item in requests_qs.values('employee_id').annotate(total=Sum('amount'))
    }

    division_stats = {}
    employee_stats: List[Dict[str, object]] = []

    category_sums = defaultdict(Decimal)
    category_counts = defaultdict(int)

    for employee in employees:
        base_salary = _as_decimal(employee.salary_amount)
        assignments_salary = _as_decimal(employee.assignments_salary_amount)
        allowances = _as_decimal(employee.allowance_total)
        recurring_amount = recurring_by_employee.get(employee.id, Decimal('0'))
        onetime_amount = onetime_by_employee.get(employee.id, Decimal('0'))
        request_amount = requests_by_employee.get(employee.id, Decimal('0'))

        total_salary = base_salary + assignments_salary
        total_payments = total_salary + allowances + recurring_amount + onetime_amount

        employee_stats.append({
            'employee': employee,
            'division': employee.division,
            'base_salary': total_salary,
            'allowances': allowances,
            'recurring': recurring_amount,
            'one_time': onetime_amount,
            'requests': request_amount,
            'total': total_payments,
        })

        division_entry = division_stats.setdefault(employee.division_id, {
            'division': employee.division,
            'total_salary': Decimal('0'),
            'allowances': Decimal('0'),
            'recurring': Decimal('0'),
            'one_time': Decimal('0'),
            'requests': Decimal('0'),
            'total': Decimal('0'),
        })
        division_entry['total_salary'] += total_salary
        division_entry['allowances'] += allowances
        division_entry['recurring'] += recurring_amount
        division_entry['one_time'] += onetime_amount
        division_entry['requests'] += request_amount
        division_entry['total'] += total_payments

        category_sums[employee.category] += total_salary
        category_counts[employee.category] += 1

    division_stats_list = sorted(division_stats.values(), key=lambda item: item['division'].name if item['division'] else '')
    employee_stats.sort(key=lambda item: item['employee'].full_name)

    def _avg(category_key: str) -> Decimal:
        total = category_sums.get(category_key, Decimal('0'))
        count = category_counts.get(category_key, 0)
        return (total / count) if count else Decimal('0')

    pps_target = Setting.get_decimal('pps_target_salary', Decimal('0'))
    aup_target = Setting.get_decimal('aup_target_salary', Decimal('61000'))

    benchmarks = [
        {
            'category': Employee.Category.PPS.label,
            'average': _avg(Employee.Category.PPS),
            'target': pps_target,
            'delta': _avg(Employee.Category.PPS) - pps_target,
        },
        {
            'category': Employee.Category.AUP.label,
            'average': _avg(Employee.Category.AUP),
            'target': aup_target,
            'delta': _avg(Employee.Category.AUP) - aup_target,
        },
    ]

    totals = {
        'recurring': sum(entry['recurring'] for entry in monthly_totals_list),
        'one_time': sum(entry['one_time'] for entry in monthly_totals_list),
        'requests': sum(entry['requests'] for entry in monthly_totals_list),
        'employees': sum(item['total'] for item in employee_stats),
    }

    allocations = BudgetAllocation.objects.select_related('budget').order_by('-created_at')[:20]

    return {
        'filters': filters,
        'monthly_totals': monthly_totals_list,
        'division_stats': division_stats_list,
        'employee_stats': employee_stats,
        'benchmarks': benchmarks,
        'totals': totals,
        'budget_allocations': allocations,
    }
