from django.urls import path

from . import views

app_name = 'budgeting'

urlpatterns = [
    path('', views.BudgetListView.as_view(), name='budget-list'),
    path('add/', views.BudgetCreateView.as_view(), name='budget-add'),
    path('<int:pk>/edit/', views.BudgetUpdateView.as_view(), name='budget-edit'),
    path('<int:budget_pk>/allocations/add/', views.BudgetAllocationCreateView.as_view(), name='allocation-add'),
    path('allocations/<int:pk>/edit/', views.BudgetAllocationUpdateView.as_view(), name='allocation-edit'),
    path('allocations/<int:pk>/delete/', views.BudgetAllocationDeleteView.as_view(), name='allocation-delete'),
]
