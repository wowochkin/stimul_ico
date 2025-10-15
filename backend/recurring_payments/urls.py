from django.urls import path

from . import views

app_name = 'recurring_payments'

urlpatterns = [
    path('periods/', views.RecurringPeriodListView.as_view(), name='period-list'),
    path('periods/add/', views.RecurringPeriodCreateView.as_view(), name='period-add'),
    path('periods/<int:pk>/', views.RecurringPeriodDetailView.as_view(), name='period-detail'),
    path('periods/<int:pk>/edit/', views.RecurringPeriodUpdateView.as_view(), name='period-edit'),
    path('periods/<int:pk>/open/', views.RecurringPeriodOpenView.as_view(), name='period-open'),
    path('periods/<int:pk>/close/', views.RecurringPeriodCloseView.as_view(), name='period-close'),
    path('periods/<int:pk>/payments/bulk/', views.RecurringPaymentBulkAssignView.as_view(), name='payment-bulk'),
    path('payments/<int:pk>/edit/', views.RecurringPaymentUpdateView.as_view(), name='payment-edit'),
    path('payments/<int:pk>/delete/', views.RecurringPaymentDeleteView.as_view(), name='payment-delete'),
]
