from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View, generic

from staffing.models import Division
from stimuli.models import Employee

from .forms import RecurringPaymentForm, RecurringPeriodCloseForm, RecurringPeriodForm
from .models import RecurringPayment, RecurringPeriod


class RecurringPeriodListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = RecurringPeriod
    template_name = 'recurring_payments/period_list.html'
    context_object_name = 'periods'
    paginate_by = 25
    permission_required = 'recurring_payments.view_recurringperiod'

    def get_queryset(self):
        return (
            RecurringPeriod.objects.prefetch_related(
                Prefetch('payments', queryset=RecurringPayment.objects.select_related('employee'))
            )
            .order_by('-start_date', '-end_date')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_form'] = RecurringPeriodForm()
        return context


class RecurringPeriodCreateView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = RecurringPeriod
    form_class = RecurringPeriodForm
    template_name = 'recurring_payments/period_form.html'
    permission_required = 'recurring_payments.add_recurringperiod'
    success_url = reverse_lazy('recurring_payments:period-list')

    def form_valid(self, form):
        messages.success(self.request, 'Период постоянных выплат создан.')
        return super().form_valid(form)


class RecurringPeriodUpdateView(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = RecurringPeriod
    form_class = RecurringPeriodForm
    template_name = 'recurring_payments/period_form.html'
    permission_required = 'recurring_payments.change_recurringperiod'

    def form_valid(self, form):
        messages.success(self.request, 'Период обновлён.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('recurring_payments:period-detail', args=[self.object.pk])


class RecurringPeriodDetailView(LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView):
    model = RecurringPeriod
    template_name = 'recurring_payments/period_detail.html'
    context_object_name = 'period'
    permission_required = 'recurring_payments.view_recurringperiod'

    def get_queryset(self):
        return (
            RecurringPeriod.objects.select_related()
            .prefetch_related(
                Prefetch(
                    'payments',
                    queryset=RecurringPayment.objects.select_related('employee').order_by('employee__full_name'),
                ),
                'budget_allocations__budget',
            )
            .order_by('-start_date')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period = self.object
        context['close_form'] = RecurringPeriodCloseForm()
        context['payments'] = period.payments.select_related('employee').order_by('employee__full_name')
        context['allocations'] = period.budget_allocations.select_related('budget')
        context['bulk_assign_url'] = reverse('recurring_payments:payment-bulk', args=[period.pk])
        return context


class RecurringPeriodOpenView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'recurring_payments.change_recurringperiod'

    def post(self, request, *args, **kwargs):
        period = get_object_or_404(RecurringPeriod, pk=kwargs['pk'])
        try:
            period.open()
            messages.success(request, 'Период открыт для редактирования.')
        except ValidationError as exc:
            messages.error(request, exc.message)
        return redirect('recurring_payments:period-detail', pk=period.pk)


class RecurringPeriodCloseView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'recurring_payments.change_recurringperiod'

    def post(self, request, *args, **kwargs):
        period = get_object_or_404(RecurringPeriod, pk=kwargs['pk'])
        form = RecurringPeriodCloseForm(request.POST)
        if form.is_valid():
            try:
                period.close(closed_by=request.user, log_message=form.cleaned_data['reason'])
                messages.success(request, 'Период закрыт, выплаты зафиксированы.')
            except ValidationError as exc:
                messages.error(request, exc.message)
        else:
            messages.error(request, 'Не удалось закрыть период. Проверьте форму.')
        return redirect('recurring_payments:period-detail', pk=period.pk)


class RecurringPaymentBulkAssignView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'recurring_payments.add_recurringpayment'
    template_name = 'recurring_payments/payment_bulk_assign.html'

    def dispatch(self, request, *args, **kwargs):
        self.period = get_object_or_404(RecurringPeriod, pk=kwargs['pk'])
        if self.period.status == RecurringPeriod.Status.CLOSED:
            messages.error(request, 'Период закрыт, изменения невозможны.')
            return redirect('recurring_payments:period-detail', pk=self.period.pk)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        division_id = request.GET.get('division')
        context = self._build_context(division_id=division_id)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        division_id = request.POST.get('division')
        employees = self._get_employees(division_id)

        if not employees:
            messages.warning(request, 'В выбранном подразделении нет сотрудников.')
            return render(request, self.template_name, self._build_context(division_id, data=request.POST))

        existing = {
            payment.employee_id: payment
            for payment in RecurringPayment.objects.select_related('employee').filter(period=self.period)
        }

        created = 0
        updated = 0
        skipped_locked: list[str] = []

        for employee in employees:
            amount_raw = (request.POST.get(f'amount_{employee.id}', '') or '').strip()
            reason = (request.POST.get(f'reason_{employee.id}', '') or '').strip()

            if not amount_raw:
                continue

            try:
                amount = Decimal(amount_raw.replace(' ', '').replace(',', '.'))
            except InvalidOperation:
                messages.error(request, f'Некорректная сумма для {employee.full_name}.')
                return render(request, self.template_name, self._build_context(division_id, data=request.POST))

            if amount <= 0:
                messages.error(request, f'Сумма выплаты для {employee.full_name} должна быть больше нуля.')
                return render(request, self.template_name, self._build_context(division_id, data=request.POST))

            if not reason:
                messages.error(request, f'Не указано основание выплаты для {employee.full_name}.')
                return render(request, self.template_name, self._build_context(division_id, data=request.POST))

            existing_payment = existing.get(employee.id)

            if existing_payment and existing_payment.is_locked:
                skipped_locked.append(employee.full_name)
                continue

            if existing_payment:
                existing_payment.amount = amount
                existing_payment.reason = reason
                existing_payment.save()
                updated += 1
            else:
                RecurringPayment.objects.create(
                    period=self.period,
                    employee=employee,
                    amount=amount,
                    reason=reason,
                )
                created += 1

        if skipped_locked:
            messages.warning(
                request,
                f'Пропущено зафиксированных выплат: {len(skipped_locked)}.',
            )

        if created or updated:
            messages.success(
                request,
                f'Сохранено выплат: {created + updated} (новых — {created}, обновлено — {updated}).',
            )
        else:
            messages.info(request, 'Изменения не внесены.')

        return redirect('recurring_payments:period-detail', pk=self.period.pk)

    def _build_context(self, division_id=None, data=None):
        divisions = Division.objects.order_by('name')
        employees = self._get_employees(division_id)
        existing = {
            payment.employee_id: payment
            for payment in RecurringPayment.objects.select_related('employee').filter(period=self.period)
        }

        data_dict = {}
        if data is not None:
            if hasattr(data, 'dict'):
                data_dict = data.dict()
            else:
                data_dict = dict(data)

        entries = []
        for employee in employees:
            payment = existing.get(employee.id)
            entries.append({
                'employee': employee,
                'amount': data_dict.get(f'amount_{employee.id}', payment.amount if payment else ''),
                'reason': data_dict.get(f'reason_{employee.id}', payment.reason if payment else ''),
                'locked': bool(payment and payment.is_locked),
            })

        return {
            'period': self.period,
            'divisions': divisions,
            'employee_entries': entries,
            'selected_division': division_id or '__all__',
        }

    def _get_employees(self, division_id):
        qs = Employee.objects.select_related('division').order_by('full_name')
        if division_id and division_id != '__all__':
            try:
                division_pk = int(division_id)
            except (TypeError, ValueError):
                return []
            qs = qs.filter(division_id=division_pk)
        return list(qs)


class RecurringPaymentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = RecurringPayment
    form_class = RecurringPaymentForm
    permission_required = 'recurring_payments.change_recurringpayment'
    template_name = 'recurring_payments/payment_form.html'

    def dispatch(self, request, *args, **kwargs):
        payment = self.get_object()
        if payment.period.status == RecurringPeriod.Status.CLOSED:
            messages.error(request, 'Выплаты закрытого периода нельзя изменять.')
            return redirect('recurring_payments:period-detail', pk=payment.period_id)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Выплата обновлена.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('recurring_payments:period-detail', args=[self.object.period_id])


class RecurringPaymentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    model = RecurringPayment
    template_name = 'recurring_payments/payment_confirm_delete.html'
    permission_required = 'recurring_payments.delete_recurringpayment'

    def dispatch(self, request, *args, **kwargs):
        payment = self.get_object()
        if payment.period.status == RecurringPeriod.Status.CLOSED:
            messages.error(request, 'Выплаты закрытого периода нельзя удалять.')
            return redirect('recurring_payments:period-detail', pk=payment.period_id)
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        period_id = self.object.period_id
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Выплата удалена.')
        return redirect('recurring_payments:period-detail', pk=period_id)
