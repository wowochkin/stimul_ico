from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View, generic

from stimuli.models import StimulusRequest
from stimuli.forms import StimulusRequestStatusForm
from stimuli.services import recompute_employee_totals

from .forms import OneTimePaymentForm, RequestCampaignForm, RequestCampaignStatusForm
from .models import OneTimePayment, RequestCampaign


class RequestCampaignListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = RequestCampaign
    template_name = 'one_time_payments/campaign_list.html'
    context_object_name = 'campaigns'
    paginate_by = 25
    permission_required = 'one_time_payments.view_requestcampaign'

    def get_queryset(self):
        queryset = RequestCampaign.objects.all().order_by('-opens_at', 'name')
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = RequestCampaign.Status.choices
        context['selected_status'] = self.request.GET.get('status', '')
        return context


class RequestCampaignCreateView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = RequestCampaign
    form_class = RequestCampaignForm
    template_name = 'one_time_payments/campaign_form.html'
    permission_required = 'one_time_payments.add_requestcampaign'
    success_url = reverse_lazy('one_time_payments:campaign-list')

    def form_valid(self, form):
        messages.success(self.request, 'Кампания создана.')
        return super().form_valid(form)


class RequestCampaignUpdateView(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = RequestCampaign
    form_class = RequestCampaignForm
    template_name = 'one_time_payments/campaign_form.html'
    permission_required = 'one_time_payments.change_requestcampaign'

    def form_valid(self, form):
        messages.success(self.request, 'Кампания обновлена.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('one_time_payments:campaign-detail', args=[self.object.pk])


class RequestCampaignDetailView(LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView):
    model = RequestCampaign
    template_name = 'one_time_payments/campaign_detail.html'
    context_object_name = 'campaign'
    permission_required = 'one_time_payments.view_requestcampaign'

    def get_queryset(self):
        return RequestCampaign.objects.prefetch_related(
            Prefetch(
                'stimulus_requests',
                queryset=StimulusRequest.objects.select_related('employee', 'requested_by').order_by('-created_at'),
            ),
            Prefetch(
                'manual_payments',
                queryset=OneTimePayment.objects.select_related('employee', 'created_by').order_by('-payment_date'),
            ),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign = self.object
        context['status_form'] = RequestCampaignStatusForm()
        context['manual_payment_form'] = OneTimePaymentForm(initial={'campaign': campaign})
        context['stimulus_status_form'] = StimulusRequestStatusForm()
        return context


class RequestCampaignStatusUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'one_time_payments.change_requestcampaign'

    def post(self, request, *args, **kwargs):
        campaign = get_object_or_404(RequestCampaign, pk=kwargs['pk'])
        form = RequestCampaignStatusForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Не удалось обновить статус кампании.')
            return redirect('one_time_payments:campaign-detail', pk=campaign.pk)

        action = form.cleaned_data['action']
        try:
            if action == 'open':
                campaign.open()
                messages.success(request, 'Кампания открыта.')
            elif action == 'close':
                campaign.close(archive=False)
                messages.success(request, 'Кампания закрыта.')
            elif action == 'archive':
                campaign.archive()
                messages.success(request, 'Кампания архивирована.')
        except ValidationError as exc:
            messages.error(request, exc.message)
        return redirect('one_time_payments:campaign-detail', pk=campaign.pk)


class ManualStimulusStatusUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'stimuli.change_stimulusrequest'

    def post(self, request, *args, **kwargs):
        campaign = get_object_or_404(RequestCampaign, pk=kwargs['pk'])
        stimulus = get_object_or_404(StimulusRequest, pk=kwargs['request_pk'], campaign=campaign)
        form = StimulusRequestStatusForm(request.POST, instance=stimulus)
        if form.is_valid():
            previous_employee_id = stimulus.employee_id
            updated_request = form.save()
            recompute_employee_totals(updated_request.employee_id)
            if previous_employee_id != updated_request.employee_id:
                recompute_employee_totals(previous_employee_id)
            messages.success(request, 'Статус заявки обновлён.')
        else:
            messages.error(request, 'Не удалось обновить заявку.')
        return redirect('one_time_payments:campaign-detail', pk=campaign.pk)


class ManualPaymentCreateView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = OneTimePayment
    form_class = OneTimePaymentForm
    template_name = 'one_time_payments/manual_payment_form.html'
    permission_required = 'one_time_payments.add_onetimepayment'

    def get_initial(self):
        initial = super().get_initial()
        campaign_id = self.kwargs.get('pk') or self.request.GET.get('campaign')
        if campaign_id:
            try:
                initial['campaign'] = RequestCampaign.objects.get(pk=campaign_id)
            except (RequestCampaign.DoesNotExist, ValueError, TypeError):
                pass
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Разовая выплата создана.')
        return super().form_valid(form)

    def form_invalid(self, form):
        campaign_id = form.data.get('campaign')
        error_text = '; '.join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]) or 'Проверьте введённые данные.'
        messages.error(self.request, f'Не удалось создать выплату. {error_text}')
        if campaign_id:
            return redirect('one_time_payments:campaign-detail', pk=campaign_id)
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        if self.object.campaign_id:
            return reverse('one_time_payments:campaign-detail', args=[self.object.campaign_id])
        return reverse('one_time_payments:manual-payment-list')


class ManualPaymentListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = OneTimePayment
    template_name = 'one_time_payments/manual_payment_list.html'
    context_object_name = 'payments'
    paginate_by = 25
    permission_required = 'one_time_payments.view_onetimepayment'

    def get_queryset(self):
        queryset = OneTimePayment.objects.select_related('employee', 'campaign', 'created_by').order_by('-payment_date', '-created_at')
        campaign_id = self.request.GET.get('campaign')
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)
            self.campaign_id = campaign_id
            self.campaign_obj = RequestCampaign.objects.filter(pk=campaign_id).first()
        else:
            self.campaign_id = None
            self.campaign_obj = None
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_campaign'] = getattr(self, 'campaign_id', None)
        context['selected_campaign_obj'] = getattr(self, 'campaign_obj', None)
        context['campaigns'] = RequestCampaign.objects.order_by('-opens_at', 'name')
        return context


class ManualPaymentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = OneTimePayment
    form_class = OneTimePaymentForm
    template_name = 'one_time_payments/manual_payment_form.html'
    permission_required = 'one_time_payments.change_onetimepayment'

    def form_valid(self, form):
        messages.success(self.request, 'Разовая выплата обновлена.')
        return super().form_valid(form)

    def get_success_url(self):
        if self.object.campaign_id:
            return reverse('one_time_payments:campaign-detail', args=[self.object.campaign_id])
        return reverse('one_time_payments:manual-payment-list')


class ManualPaymentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    model = OneTimePayment
    template_name = 'one_time_payments/manual_payment_confirm_delete.html'
    permission_required = 'one_time_payments.delete_onetimepayment'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        campaign_id = self.object.campaign_id
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Разовая выплата удалена.')
        if campaign_id:
            return redirect('one_time_payments:campaign-detail', pk=campaign_id)
        return redirect('one_time_payments:manual-payment-list')

    def get_success_url(self):
        if self.object.campaign_id:
            return reverse('one_time_payments:campaign-detail', args=[self.object.campaign_id])
        return reverse('one_time_payments:manual-payment-list')
