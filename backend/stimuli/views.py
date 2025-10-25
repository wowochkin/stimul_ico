from decimal import Decimal
import io
import logging
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import BooleanField, Case, Value, When
from django.http import Http404, QueryDict, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View, generic
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from .filters import EmployeeFilter, StimulusRequestFilter
from .forms import EmployeeForm, InternalAssignmentFormSet, StimulusRequestForm, StimulusRequestStatusForm, EmployeeExcelUploadForm
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


class EmployeeExcelTemplateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Представление для скачивания Excel шаблона с актуальными данными сотрудников"""
    permission_required = 'stimuli.view_employee'
    logger = logging.getLogger('stimuli')

    def get(self, request, *args, **kwargs):
        self.logger.info(f"User {request.user.username} downloading Excel template")
        # Создаем новую рабочую книгу
        wb = Workbook()
        ws = wb.active
        ws.title = "Сотрудники"

        # Получаем все подразделения и должности для справочников
        divisions = Division.objects.all().order_by('name')
        positions = Position.objects.all().order_by('name')

        # Создаем заголовки - включаем все доступные столбцы
        headers = [
            'ФИО',
            'Подразделение',
            'Должность', 
            'Категория',
            'Ставка',
            'Оклад',
            'Выплаты по ставке',
            'Совмещения',
            'Оклад совмещений',
            'Итого базовых выплат',
            'Надбавка',
            'Основание надбавки',
            'Срок надбавки',
            'Выплата',
            'Обоснование',
            'Итого выплат'
        ]

        # Стили для заголовков
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")

        # Записываем заголовки
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

        # Получаем всех сотрудников с их данными
        employees = Employee.objects.select_related('division', 'position').order_by('full_name')
        
        # Записываем данные сотрудников
        for row, employee in enumerate(employees, 2):
            col = 1
            ws.cell(row=row, column=col, value=employee.full_name)
            col += 1
            ws.cell(row=row, column=col, value=employee.division.name if employee.division else '')
            col += 1
            ws.cell(row=row, column=col, value=employee.position.name if employee.position else '')
            col += 1
            ws.cell(row=row, column=col, value=employee.category)
            col += 1
            ws.cell(row=row, column=col, value=float(employee.rate))
            col += 1
            ws.cell(row=row, column=col, value=float(employee.position.base_salary) if employee.position else 0.0)
            col += 1
            ws.cell(row=row, column=col, value=float(employee.salary_amount))
            col += 1
            # Совмещения - текстовое описание
            assignments_text = ''
            if employee.assignments.exists():
                assignments_list = []
                for assignment in employee.assignments.all():
                    assignment_desc = f"{assignment.position.name} ({assignment.rate})"
                    if assignment.allowance_amount:
                        assignment_desc += f" + надбавка {assignment.allowance_amount}"
                    assignments_list.append(assignment_desc)
                assignments_text = '; '.join(assignments_list)
            ws.cell(row=row, column=col, value=assignments_text)
            col += 1
            ws.cell(row=row, column=col, value=float(employee.assignments_salary_amount))
            col += 1
            ws.cell(row=row, column=col, value=float(employee.total_salary_amount))
            col += 1
            ws.cell(row=row, column=col, value=float(employee.allowance_total))
            col += 1
            ws.cell(row=row, column=col, value=employee.allowance_reason)
            col += 1
            ws.cell(row=row, column=col, value=employee.allowance_until.strftime('%d.%m.%Y') if employee.allowance_until else '')
            col += 1
            ws.cell(row=row, column=col, value=float(employee.payment))
            col += 1
            ws.cell(row=row, column=col, value=employee.justification)
            col += 1
            ws.cell(row=row, column=col, value=float(employee.total_payments))

        # Создаем лист со справочниками
        ws_div = wb.create_sheet("Подразделения")
        ws_div.cell(row=1, column=1, value="Название подразделения").font = header_font
        ws_div.cell(row=1, column=1).fill = header_fill
        
        for row, division in enumerate(divisions, 2):
            ws_div.cell(row=row, column=1, value=division.name)

        ws_pos = wb.create_sheet("Должности")
        ws_pos.cell(row=1, column=1, value="Название должности").font = header_font
        ws_pos.cell(row=1, column=2, value="Оклад").font = header_font
        ws_pos.cell(row=1, column=1).fill = header_fill
        ws_pos.cell(row=1, column=2).fill = header_fill
        
        for row, position in enumerate(positions, 2):
            ws_pos.cell(row=row, column=1, value=position.name)
            ws_pos.cell(row=row, column=2, value=float(position.base_salary))

        # Создаем лист с категориями
        ws_cat = wb.create_sheet("Категории")
        ws_cat.cell(row=1, column=1, value="Код").font = header_font
        ws_cat.cell(row=1, column=2, value="Название").font = header_font
        ws_cat.cell(row=1, column=1).fill = header_fill
        ws_cat.cell(row=1, column=2).fill = header_fill
        
        categories = Employee.Category.choices
        for row, (code, name) in enumerate(categories, 2):
            ws_cat.cell(row=row, column=1, value=str(code))
            ws_cat.cell(row=row, column=2, value=str(name))

        # Настраиваем ширину колонок
        for ws_sheet in [ws, ws_div, ws_pos, ws_cat]:
            for column in ws_sheet.columns:
                max_length = 0
                column_letter = get_column_letter(column[0].column)
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except (TypeError, AttributeError):
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws_sheet.column_dimensions[column_letter].width = adjusted_width

        # Сохраняем в память
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        # Создаем HTTP ответ
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"employees_template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response


class EmployeeExcelUploadView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Представление для загрузки Excel файла с обновленными данными сотрудников"""
    permission_required = 'stimuli.add_employee'
    template_name = 'stimuli/employee_upload.html'
    logger = logging.getLogger('stimuli')

    def get(self, request, *args, **kwargs):
        form = EmployeeExcelUploadForm()
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):
        form = EmployeeExcelUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return self.render_to_response({'form': form})

        excel_file = form.cleaned_data['excel_file']
        sync_mode = form.cleaned_data['sync_mode']
        
        self.logger.info(f"User {request.user.username} uploading Excel file: {excel_file.name}, sync_mode: {sync_mode}")

        try:
            from openpyxl import load_workbook
            
            # Загружаем рабочую книгу
            wb = load_workbook(excel_file)
            ws = wb.active
            
            # Получаем справочники
            divisions_dict = {d.name: d for d in Division.objects.all()}
            positions_dict = {p.name: p for p in Position.objects.all()}
            
            # Создаем словарь категорий для обработки как кодов, так и отображаемых названий
            category_dict = {}
            for code, display_name in Employee.Category.choices:
                category_dict[code] = code  # Код категории
                category_dict[display_name] = code  # Отображаемое название
            
            created_count = 0
            updated_count = 0
            deleted_count = 0
            errors = []
            processed_employee_names = set()  # Для отслеживания обработанных сотрудников

            # Обрабатываем строки начиная со второй (пропускаем заголовки)
            for row_num in range(2, ws.max_row + 1):
                try:
                    # Читаем данные из строки (только основные поля для редактирования)
                    full_name = ws.cell(row=row_num, column=1).value
                    if not full_name or not str(full_name).strip():
                        continue
                    
                    division_name = ws.cell(row=row_num, column=2).value
                    position_name = ws.cell(row=row_num, column=3).value
                    category_code = ws.cell(row=row_num, column=4).value
                    rate = ws.cell(row=row_num, column=5).value
                    # Пропускаем столбцы 6-9 (вычисляемые поля)
                    allowance_amount = ws.cell(row=row_num, column=11).value
                    allowance_reason = ws.cell(row=row_num, column=12).value
                    allowance_until = ws.cell(row=row_num, column=13).value
                    payment = ws.cell(row=row_num, column=14).value
                    justification = ws.cell(row=row_num, column=15).value

                    # Валидация и преобразование данных
                    if not division_name or division_name not in divisions_dict:
                        errors.append(f"Строка {row_num}: Подразделение '{division_name}' не найдено")
                        continue
                    
                    if not position_name or position_name not in positions_dict:
                        errors.append(f"Строка {row_num}: Должность '{position_name}' не найдена")
                        continue
                    
                    if not category_code or category_code not in category_dict:
                        errors.append(f"Строка {row_num}: Неверная категория '{category_code}'")
                        continue
                    
                    # Получаем правильный код категории
                    actual_category_code = category_dict[category_code]

                    # Преобразуем числовые значения
                    try:
                        rate = float(rate) if rate is not None else 1.0
                        allowance_amount = float(allowance_amount) if allowance_amount is not None else 0.0
                        payment = float(payment) if payment is not None else 0.0
                    except (ValueError, TypeError) as e:
                        errors.append(f"Строка {row_num}: Некорректные числовые значения - {str(e)}")
                        continue

                    # Преобразуем дату
                    allowance_until_date = None
                    if allowance_until:
                        try:
                            if isinstance(allowance_until, str):
                                allowance_until_date = datetime.strptime(allowance_until, '%d.%m.%Y').date()
                            else:
                                allowance_until_date = allowance_until.date() if hasattr(allowance_until, 'date') else allowance_until
                        except ValueError:
                            errors.append(f"Строка {row_num}: Некорректный формат даты")
                            continue

                    # Проверяем, существует ли сотрудник
                    employee, created = Employee.objects.get_or_create(
                        full_name=str(full_name).strip(),
                        defaults={
                            'division': divisions_dict[division_name],
                            'position': positions_dict[position_name],
                            'category': actual_category_code,
                            'rate': rate,
                            'allowance_amount': allowance_amount,
                            'allowance_reason': str(allowance_reason).strip() if allowance_reason else '',
                            'allowance_until': allowance_until_date,
                            'payment': payment,
                            'justification': str(justification).strip() if justification else '',
                        }
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        # Обновляем существующего сотрудника
                        employee.division = divisions_dict[division_name]
                        employee.position = positions_dict[position_name]
                        employee.category = actual_category_code
                        employee.rate = rate
                        employee.allowance_amount = allowance_amount
                        employee.allowance_reason = str(allowance_reason).strip() if allowance_reason else ''
                        employee.allowance_until = allowance_until_date
                        employee.payment = payment
                        employee.justification = str(justification).strip() if justification else ''
                        employee.save()
                        updated_count += 1
                    
                    # Добавляем в список обработанных сотрудников
                    processed_employee_names.add(str(full_name).strip())

                except (ValueError, TypeError, AttributeError) as e:
                    errors.append(f"Строка {row_num}: Ошибка обработки - {str(e)}")
                    continue

            # Если выбран режим полной синхронизации, удаляем сотрудников, которых нет в файле
            if sync_mode == 'full_sync':
                all_employees = Employee.objects.all()
                for employee in all_employees:
                    if employee.full_name not in processed_employee_names:
                        employee.delete()
                        deleted_count += 1

            # Формируем сообщения для пользователя
            if created_count > 0:
                messages.success(request, f'Создано новых сотрудников: {created_count}')
            if updated_count > 0:
                messages.success(request, f'Обновлено сотрудников: {updated_count}')
            if deleted_count > 0:
                messages.success(request, f'Удалено сотрудников: {deleted_count}')
            
            self.logger.info(f"Excel processing completed: created={created_count}, updated={updated_count}, deleted={deleted_count}, errors={len(errors)}")
            
            if errors:
                error_message = 'Ошибки при обработке файла:\n' + '\n'.join(errors[:10])
                if len(errors) > 10:
                    error_message += f'\n... и еще {len(errors) - 10} ошибок'
                messages.error(request, error_message)
            
            if created_count == 0 and updated_count == 0 and deleted_count == 0 and not errors:
                messages.info(request, 'Не найдено данных для обработки.')

        except (ValueError, TypeError, AttributeError, IOError) as e:
            messages.error(request, f'Ошибка при обработке файла: {str(e)}')

        return self.render_to_response({'form': form})

    def render_to_response(self, context):
        from django.shortcuts import render
        return render(self.request, self.template_name, context)
