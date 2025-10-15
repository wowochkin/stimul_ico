from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import generic

from .forms import BudgetAllocationForm, BudgetForm
from .models import Budget, BudgetAllocation


class BudgetListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Budget
    template_name = 'budgeting/budget_list.html'
    context_object_name = 'budgets'
    paginate_by = 25
    permission_required = 'budgeting.view_budget'

    def get_queryset(self):
        return Budget.objects.prefetch_related(
            Prefetch(
                'allocations',
                queryset=BudgetAllocation.objects.select_related('recurring_period', 'campaign').order_by('-created_at'),
            )
        ).order_by('-year', '-month', 'budget_type')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['budget_form'] = BudgetForm()
        context['allocation_form'] = BudgetAllocationForm()
        return context


class BudgetCreateView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'budgeting/budget_form.html'
    permission_required = 'budgeting.add_budget'
    success_url = reverse_lazy('budgeting:budget-list')

    def form_valid(self, form):
        messages.success(self.request, 'Бюджет создан.')
        return super().form_valid(form)


class BudgetUpdateView(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'budgeting/budget_form.html'
    permission_required = 'budgeting.change_budget'

    def form_valid(self, form):
        messages.success(self.request, 'Бюджет обновлён.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('budgeting:budget-list')


class BudgetAllocationCreateView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = BudgetAllocation
    form_class = BudgetAllocationForm
    template_name = 'budgeting/allocation_form.html'
    permission_required = 'budgeting.add_budgetallocation'

    def dispatch(self, request, *args, **kwargs):
        self.budget = get_object_or_404(Budget, pk=kwargs['budget_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial['budget'] = self.budget
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['budget'].initial = self.budget
        form.fields['budget'].widget = form.fields['budget'].hidden_widget()
        return form

    def form_valid(self, form):
        form.instance.budget = self.budget
        messages.success(self.request, 'Выделение бюджета создано.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('budgeting:budget-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['budget'] = self.budget
        return context


class BudgetAllocationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = BudgetAllocation
    form_class = BudgetAllocationForm
    template_name = 'budgeting/allocation_form.html'
    permission_required = 'budgeting.change_budgetallocation'

    def form_valid(self, form):
        messages.success(self.request, 'Выделение бюджета обновлено.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('budgeting:budget-list')


class BudgetAllocationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    model = BudgetAllocation
    template_name = 'budgeting/allocation_confirm_delete.html'
    permission_required = 'budgeting.delete_budgetallocation'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Выделение бюджета удалено.')
        return redirect('budgeting:budget-list')
