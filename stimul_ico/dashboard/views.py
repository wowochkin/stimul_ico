import csv
import json
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.urls import reverse
from django.views import View, generic

from .forms import DashboardFilterForm
from .services import DashboardFilters, collect_dashboard_metrics


class DashboardView(LoginRequiredMixin, PermissionRequiredMixin, generic.TemplateView):
    template_name = 'dashboard/dashboard_overview.html'
    permission_required = 'dashboard.view_dashboard'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = DashboardFilterForm(self.request.GET or None)
        if form.is_valid():
            filters = DashboardFilters(
                start_date=form.cleaned_data.get('start_date'),
                end_date=form.cleaned_data.get('end_date'),
                division_id=form.cleaned_data.get('division').id if form.cleaned_data.get('division') else None,
                employee_id=form.cleaned_data.get('employee').id if form.cleaned_data.get('employee') else None,
            )
        else:
            filters = DashboardFilters()
        metrics = collect_dashboard_metrics(filters)
        context.update(metrics)

        chart_data = self._build_chart_data(metrics)
        context['chart_data_json'] = json.dumps(chart_data, ensure_ascii=False)
        context['filter_form'] = form
        context['export_url'] = reverse('dashboard:export')
        return context

    @staticmethod
    def _build_chart_data(metrics):
        def to_float(value):
            if isinstance(value, Decimal):
                return float(value)
            if value is None:
                return 0.0
            return float(value)

        def to_text(value):
            if value is None:
                return ''
            return str(value)

        monthly_labels = []
        monthly_recurring = []
        monthly_one_time = []
        monthly_requests = []

        for row in metrics.get('monthly_totals', []):
            month = row.get('month')
            label = month.strftime('%Y-%m') if month else 'Без даты'
            monthly_labels.append(label)
            monthly_recurring.append(to_float(row.get('recurring', 0)))
            monthly_one_time.append(to_float(row.get('one_time', 0)))
            monthly_requests.append(to_float(row.get('requests', 0)))

        def aggregate_entries(entries, limit, keys):
            if not entries:
                return entries
            entries = sorted(entries, key=lambda item: item.get('total', 0), reverse=True)
            if len(entries) <= limit:
                return entries
            top = entries[:limit]
            rest = entries[limit:]
            aggregated = {'label': 'Прочие', 'total': 0}
            for key in keys:
                aggregated[key] = 0
            for entry in rest:
                aggregated['total'] += entry.get('total', 0)
                for key in keys:
                    aggregated[key] += entry.get(key, 0)
            return top + [aggregated]

        division_entries = []
        for entry in metrics.get('division_stats', []):
            division = entry.get('division')
            division_entries.append({
                'label': to_text(getattr(division, 'name', 'Без подразделения')),
                'total': to_float(entry.get('total', 0)),
                'base': to_float(entry.get('total_salary', 0)),
                'allowances': to_float(entry.get('allowances', 0)),
                'recurring': to_float(entry.get('recurring', 0)),
                'one_time': to_float(entry.get('one_time', 0)),
                'requests': to_float(entry.get('requests', 0)),
            })

        division_entries = aggregate_entries(division_entries, limit=6, keys=['base', 'allowances', 'recurring', 'one_time', 'requests'])
        division_labels = [entry['label'] for entry in division_entries]
        division_totals = [entry['total'] for entry in division_entries]

        employee_entries = []
        for entry in metrics.get('employee_stats', []):
            employee_entries.append({
                'label': to_text(entry['employee'].full_name),
                'total': to_float(entry.get('total', 0)),
            })
        employee_entries = aggregate_entries(employee_entries, limit=8, keys=[])
        employee_labels = [entry['label'] for entry in employee_entries]
        employee_totals = [entry['total'] for entry in employee_entries]

        category_labels = []
        category_average = []
        category_target = []
        for bench in metrics.get('benchmarks', []):
            category_labels.append(to_text(bench.get('category')))
            category_average.append(to_float(bench.get('average', 0)))
            category_target.append(to_float(bench.get('target', 0)))

        totals = metrics.get('totals', {})
        totals_breakdown_values = [
            to_float(totals.get('recurring', 0)),
            to_float(totals.get('one_time', 0)),
            to_float(totals.get('requests', 0)),
        ]

        return {
            'monthly': {
                'labels': monthly_labels,
                'recurring': monthly_recurring,
                'one_time': monthly_one_time,
                'requests': monthly_requests,
            },
            'division': {
                'labels': division_labels,
                'totals': division_totals,
            },
            'employees': {
                'labels': employee_labels,
                'totals': employee_totals,
            },
            'division_breakdown': {
                'labels': [entry['label'] for entry in division_entries],
                'base': [entry.get('base', 0) for entry in division_entries],
                'allowances': [entry.get('allowances', 0) for entry in division_entries],
                'recurring': [entry.get('recurring', 0) for entry in division_entries],
                'one_time': [entry.get('one_time', 0) for entry in division_entries],
                'requests': [entry.get('requests', 0) for entry in division_entries],
            },
            'category': {
                'labels': category_labels,
                'average': category_average,
                'target': category_target,
            },
            'totals_breakdown': {
                'labels': ['Постоянные', 'Разовые', 'Заявки'],
                'values': totals_breakdown_values,
            },
        }


class DashboardExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.view_dashboard'

    def get(self, request, *args, **kwargs):
        form = DashboardFilterForm(request.GET or None)
        if form.is_valid():
            filters = DashboardFilters(
                start_date=form.cleaned_data.get('start_date'),
                end_date=form.cleaned_data.get('end_date'),
                division_id=form.cleaned_data.get('division').id if form.cleaned_data.get('division') else None,
                employee_id=form.cleaned_data.get('employee').id if form.cleaned_data.get('employee') else None,
            )
        else:
            filters = DashboardFilters()
        metrics = collect_dashboard_metrics(filters)

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        response['Content-Disposition'] = f'attachment; filename="dashboard_{timestamp}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Месяц', 'Постоянные выплаты', 'Разовые выплаты', 'Заявки'])
        for row in metrics['monthly_totals']:
            month_value = row['month'].strftime('%Y-%m') if row['month'] else ''
            writer.writerow([month_value, row['recurring'], row['one_time'], row['requests']])
        return response
