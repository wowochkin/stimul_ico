from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import BooleanField, Case, Sum, Value, When
from django.http import Http404, QueryDict
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View, generic

from .filters import EmployeeFilter, StimulusRequestFilter
from .forms import EmployeeForm, InternalAssignmentFormSet, StimulusRequestForm, StimulusRequestStatusForm
from one_time_payments.models import RequestCampaign
from staffing.models import Division, Position
from .models import Employee, StimulusRequest
from .services import recompute_employee_totals


class EmployeeListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Employee
    template_name = 'stimuli/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 25
    permission_required = 'stimuli.view_employee'
    AVAILABLE_COLUMNS = [
        ('division', 'Подразделение'),
        ('position', 'Должность'),
        ('base_salary', 'Оклад'),
        ('rate', 'Ставка'),
        ('salary', 'Выплаты по ставке'),
        ('assignments', 'Совмещения'),
        ('assignments_salary', 'Оклад совмещений'),
        ('total_salary', 'Итого базовых выплат'),
        ('allowance_amount', 'Надбавка'),
        ('allowance_reason', 'Основание надбавки'),
        ('allowance_until', 'Срок надбавки'),
        ('payment', 'Выплата'),
        ('justification', 'Обоснование'),
        ('total_payments', 'Итого выплат'),
    ]
    DEFAULT_COLUMNS = [
        'division',
        'position',
        'base_salary',
        'rate',
        'salary',
        'assignments',
        'assignments_salary',
        'total_salary',
        'allowance_amount',
        'allowance_reason',
        'allowance_until',
        'payment',
        'justification',
        'total_payments',
    ]

    def get_paginate_by(self, queryset):
        if self.request.GET.get('show') == 'all':
            return None
        return self.paginate_by

    def get_queryset(self):
        qs = Employee.objects.select_related('division', 'position').prefetch_related('requests__requested_by', 'assignments__position')
        self.filterset = EmployeeFilter(self.request.GET or None, queryset=qs)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = getattr(
            self,
            'filterset',
            EmployeeFilter(None, queryset=self.model.objects.all())
        )
        selected_columns = self.get_selected_columns()
        user = self.request.user
        show_all = self.request.GET.get('show') == 'all'
        context.update({
            'available_columns': self.AVAILABLE_COLUMNS,
            'selected_columns': selected_columns,
            'show_all': show_all,
            'show_all_url': self._build_query(show='all'),
            'paginate_url': self._build_query(show=None),
        })
        extra_cols = 1 + len(selected_columns)
        if user.has_perm('stimuli.change_employee'):
            extra_cols += 1
        context['table_colspan'] = extra_cols
        return context

    def get_selected_columns(self):
        valid_keys = [key for key, _ in self.AVAILABLE_COLUMNS]
        requested = self.request.GET.getlist('columns')
        if requested:
            selected = [key for key in requested if key in valid_keys]
        else:
            selected = list(self.DEFAULT_COLUMNS)
        if not selected:
            selected = list(self.DEFAULT_COLUMNS)
        return selected

    def _build_query(self, **updates):
        params = self.request.GET.copy()
        for key, value in updates.items():
            if value is None:
                params.pop(key, None)
            else:
                params[key] = value
        encoded = params.urlencode()
        return '?' + encoded if encoded else ''


class EmployeeCreateView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'stimuli/employee_form.html'
    permission_required = 'stimuli.add_employee'
    success_url = reverse_lazy('employee-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['assignment_formset'] = InternalAssignmentFormSet(self.request.POST)
        else:
            context['assignment_formset'] = InternalAssignmentFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        assignment_formset = context['assignment_formset']
        if assignment_formset.is_valid():
            self.object = form.save()
            assignment_formset.instance = self.object
            assignment_formset.save()
            return redirect(self.success_url)
        return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


class EmployeeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'stimuli/employee_form.html'
    permission_required = 'stimuli.change_employee'
    success_url = reverse_lazy('employee-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['assignment_formset'] = InternalAssignmentFormSet(self.request.POST, instance=self.object)
        else:
            context['assignment_formset'] = InternalAssignmentFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        assignment_formset = context['assignment_formset']
        if assignment_formset.is_valid():
            self.object = form.save()
            assignment_formset.instance = self.object
            assignment_formset.save()
            return redirect(self.success_url)
        return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


class EmployeeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    model = Employee
    template_name = 'stimuli/employee_confirm_delete.html'
    permission_required = 'stimuli.delete_employee'
    success_url = reverse_lazy('employee-list')


class StimulusRequestListView(LoginRequiredMixin, generic.ListView):
    model = StimulusRequest
    template_name = 'stimuli/request_list.html'
    context_object_name = 'requests'
    paginate_by = 25

    def get_queryset(self):
        qs = StimulusRequest.objects.select_related('employee', 'requested_by', 'campaign')
        if self.request.user.has_perm('stimuli.view_all_requests'):
            base_qs = qs
        else:
            base_qs = qs.filter(requested_by=self.request.user)
        self.filterset = StimulusRequestFilter(self.request.GET or None, queryset=base_qs)
        filtered_qs = self.filterset.qs
        user = self.request.user
        if user.has_perm('stimuli.view_all_requests') or user.has_perm('stimuli.change_stimulusrequest'):
            return filtered_qs.annotate(
                can_edit=Value(True, output_field=BooleanField()),
                can_delete=Value(True, output_field=BooleanField()),
            )

        if not user.has_perm('stimuli.edit_pending_requests'):
            return filtered_qs.annotate(
                can_edit=Value(False, output_field=BooleanField()),
                can_delete=Value(False, output_field=BooleanField()),
            )

        return filtered_qs.annotate(
            can_edit=Case(
                When(
                    status=StimulusRequest.Status.PENDING,
                    requested_by=user,
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            ),
            can_delete=Case(
                When(
                    status=StimulusRequest.Status.PENDING,
                    requested_by=user,
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            ),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        user = self.request.user
        can_bulk_delete = user.has_perm('stimuli.delete_stimulusrequest') or user.has_perm('stimuli.edit_pending_requests')
        show_manage = user.has_perm('stimuli.change_stimulusrequest') or user.has_perm('stimuli.edit_pending_requests')
        context['can_bulk_delete'] = can_bulk_delete
        context['show_manage_column'] = show_manage
        base_columns = 8
        if can_bulk_delete:
            base_columns += 1
        if show_manage:
            base_columns += 1
        context['table_colspan'] = base_columns
        return context


class StimulusRequestCreateView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = StimulusRequest
    form_class = StimulusRequestForm
    template_name = 'stimuli/request_form.html'
    success_url = reverse_lazy('request-list')
    permission_required = 'stimuli.add_stimulusrequest'

    def form_valid(self, form):
        form.instance.requested_by = self.request.user
        response = super().form_valid(form)
        recompute_employee_totals(self.object.employee_id)
        messages.success(self.request, 'Заявка создана.')
        return response


class StimulusRequestUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = StimulusRequest
    form_class = StimulusRequestForm
    template_name = 'stimuli/request_form.html'
    success_url = reverse_lazy('request-list')

    def form_valid(self, form):
        instance = self.get_object()
        previous_employee_id = instance.employee_id
        response = super().form_valid(form)
        recompute_employee_totals(self.object.employee_id)
        if previous_employee_id != self.object.employee_id:
            recompute_employee_totals(previous_employee_id)
        messages.success(self.request, 'Заявка обновлена.')
        return response

    def get_queryset(self):
        base_qs = StimulusRequest.objects.select_related('employee', 'requested_by')
        user = self.request.user
        if user.has_perm('stimuli.view_all_requests') or user.has_perm('stimuli.change_stimulusrequest'):
            return base_qs
        if user.has_perm('stimuli.edit_pending_requests'):
            return base_qs.filter(requested_by=user, status=StimulusRequest.Status.PENDING)
        return base_qs.none()

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except Http404:
            messages.error(request, 'У вас нет прав для редактирования этой заявки.')
            return redirect('request-list')


class StimulusRequestStatusUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'stimuli.change_stimulusrequest'

    def post(self, request, *args, **kwargs):
        instance = get_object_or_404(StimulusRequest, pk=kwargs['pk'])
        form = StimulusRequestStatusForm(request.POST, instance=instance)
        if form.is_valid():
            with transaction.atomic():
                updated_request = form.save()
                recompute_employee_totals(updated_request.employee_id)
            messages.success(request, 'Статус заявки обновлён.')
        else:
            messages.error(request, 'Не удалось обновить статус заявки. Проверьте корректность данных.')
        return redirect('request-list')


class StimulusRequestDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = StimulusRequest
    template_name = 'stimuli/request_confirm_delete.html'
    success_url = reverse_lazy('request-list')

    def get_queryset(self):
        return deletable_requests_queryset(self.request.user)

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except Http404:
            messages.error(request, 'У вас нет прав для удаления этой заявки.')
            return redirect('request-list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        employee_id = self.object.employee_id
        response = super().delete(request, *args, **kwargs)
        recompute_employee_totals(employee_id)
        messages.success(request, 'Заявка удалена.')
        return response


class HomeRedirectView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        if request.user.has_perm('stimuli.view_employee'):
            return redirect('employee-list')
        return redirect('request-list')


class StimulusRequestBulkDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy('request-list')

    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist('selected_requests')
        if not ids:
            messages.warning(request, 'Не выбраны заявки для удаления.')
            return redirect(self.success_url)

        deletable_qs = deletable_requests_queryset(request.user).filter(pk__in=ids)
        deletable_ids = list(deletable_qs.values_list('pk', flat=True))

        if not deletable_ids:
            messages.error(request, 'Нет прав на удаление выбранных заявок.')
            return redirect(self.success_url)

        employees_to_update = list(deletable_qs.values_list('employee_id', flat=True))
        deleted_count, _ = deletable_qs.delete()

        for employee_id in set(employees_to_update):
            recompute_employee_totals(employee_id)

        messages.success(request, f'Удалено заявок: {deleted_count}.')
        return redirect(self.success_url)


class StimulusRequestBulkCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'stimuli.add_stimulusrequest'
    template_name = 'stimuli/request_bulk_create.html'

    def get_divisions(self):
        return Division.objects.order_by('name')

    def get_campaigns(self):
        return RequestCampaign.objects.order_by('-opens_at', 'name')

    def get(self, request, *args, **kwargs):
        division_id = request.GET.get('division')
        campaign_id = request.GET.get('campaign')
        context = self._build_context(division_id, campaign_id=campaign_id)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        division_id = request.POST.get('division')
        campaign_id = request.POST.get('campaign')
        employees_qs = Employee.objects.select_related('division').order_by('full_name')
        if division_id and division_id != '__all__':
            try:
                division_pk = int(division_id)
            except (TypeError, ValueError):
                messages.error(request, 'Некорректное подразделение.')
                return self.render_to_response(self._build_context(None, campaign_id=campaign_id))
            employees_qs = employees_qs.filter(division_id=division_pk)
        employees = list(employees_qs)
        if not employees:
            messages.warning(request, 'В выбранном подразделении нет сотрудников.')
            return self.render_to_response(self._build_context(None, campaign_id=campaign_id))

        campaign = None
        if campaign_id:
            try:
                campaign_pk = int(campaign_id)
                campaign = RequestCampaign.objects.get(pk=campaign_pk)
                if campaign.status == RequestCampaign.Status.DRAFT:
                    messages.error(request, 'Кампания в статусе "Черновик" недоступна для заявок.')
                    return self.render_to_response(self._build_context(division_id, employees, request.POST, campaign_id=campaign_id))
            except (TypeError, ValueError, RequestCampaign.DoesNotExist):
                messages.error(request, 'Некорректная кампания.')
                return self.render_to_response(self._build_context(division_id, employees, request.POST, campaign_id=campaign_id))

        created = 0
        affected_employees = []
        for employee in employees:
            amount_raw = request.POST.get(f'amount_{employee.id}', '').strip()
            justification = request.POST.get(f'justification_{employee.id}', '').strip()
            if not amount_raw:
                continue
            try:
                amount = Decimal(amount_raw.replace(' ', '').replace(',', '.'))
            except Exception:
                messages.error(request, f'Некорректная сумма для {employee.full_name}.')
                return self.render_to_response(self._build_context(division_id, employees, request.POST, campaign_id=campaign_id))

            if amount <= 0:
                continue

            if not justification:
                messages.error(request, f'Обоснование обязательно для {employee.full_name}.')
                return self.render_to_response(self._build_context(division_id, employees, request.POST, campaign_id=campaign_id))

            StimulusRequest.objects.create(
                employee=employee,
                requested_by=request.user,
                amount=amount,
                justification=justification,
                campaign=campaign,
            )
            created += 1
            affected_employees.append(employee.id)

        for employee_id in set(affected_employees):
            recompute_employee_totals(employee_id)

        if created:
            messages.success(request, f'Создано заявок: {created}.')
            return redirect('request-list')

        messages.info(request, 'Не выбраны сотрудники для создания заявок.')
        return self.render_to_response(self._build_context(division_id, employees, request.POST, campaign_id=campaign_id))

    def _build_context(self, division_id=None, employees=None, data=None, campaign_id=None):
        divisions = list(self.get_divisions())
        campaigns = list(self.get_campaigns())
        employees = employees or self._get_employees_for_division(division_id)
        data = data or {}
        if isinstance(data, QueryDict):
            data = data.dict()

        selected_campaign = campaign_id if campaign_id is not None else data.get('campaign', '')

        entries = []
        for employee in employees:
            entries.append({
                'employee': employee,
                'amount': data.get(f'amount_{employee.id}', ''),
                'justification': data.get(f'justification_{employee.id}', ''),
            })

        return {
            'divisions': divisions,
            'campaigns': campaigns,
            'selected_division': division_id,
            'selected_campaign': selected_campaign,
            'employee_entries': entries,
        }

    def _get_employees_for_division(self, division_id):
        qs = Employee.objects.select_related('division').order_by('full_name')
        if division_id and division_id != '__all__':
            try:
                division_pk = int(division_id)
            except (TypeError, ValueError):
                return []
            qs = qs.filter(division_id=division_pk)
        return list(qs)

    def render_to_response(self, context):
        from django.shortcuts import render

        return render(self.request, self.template_name, context)


def deletable_requests_queryset(user):
    base_qs = StimulusRequest.objects.select_related('employee', 'requested_by')
    if user.has_perm('stimuli.delete_stimulusrequest') or user.has_perm('stimuli.view_all_requests'):
        return base_qs
    if user.has_perm('stimuli.edit_pending_requests'):
        return base_qs.filter(requested_by=user, status=StimulusRequest.Status.PENDING)
    return base_qs.none()
