from __future__ import annotations

from decimal import Decimal
from typing import Union

from django.db import transaction
from django.db.models import Sum

from .models import Employee, StimulusRequest


def _as_employee_id(employee: Union[Employee, int]) -> int:
    return employee.pk if isinstance(employee, Employee) else int(employee)


def recompute_employee_totals(employee: Union[Employee, int]) -> None:
    employee_id = _as_employee_id(employee)

    with transaction.atomic():
        employee_obj = Employee.objects.select_for_update().get(pk=employee_id)

        approved_qs = StimulusRequest.objects.filter(
            employee_id=employee_id,
            status=StimulusRequest.Status.APPROVED,
        )
        totals = approved_qs.aggregate(total=Sum('amount'))
        employee_obj.payment = totals['total'] or Decimal('0')

        requests_qs = StimulusRequest.objects.filter(employee_id=employee_id).select_related('requested_by').order_by('-created_at')

        summary_lines: list[str] = []
        for index, request in enumerate(requests_qs, start=1):
            responsible = request.requested_by.get_full_name() or request.requested_by.username
            justification = (request.justification or '').strip() or '—'
            amount_display = f"{request.amount:.2f}".replace('.', ',')
            summary_lines.append(
                f"{index}. {amount_display} ₽ — {request.get_status_display()} ({responsible}) — {justification}"
            )

        employee_obj.justification = '\n'.join(summary_lines) if summary_lines else ''
        employee_obj.save(update_fields=['payment', 'justification'])
