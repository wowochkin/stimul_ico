from django.urls import path

from . import views

app_name = 'one_time_payments'

urlpatterns = [
    path('campaigns/', views.RequestCampaignListView.as_view(), name='campaign-list'),
    path('campaigns/add/', views.RequestCampaignCreateView.as_view(), name='campaign-add'),
    path('campaigns/<int:pk>/', views.RequestCampaignDetailView.as_view(), name='campaign-detail'),
    path('campaigns/<int:pk>/edit/', views.RequestCampaignUpdateView.as_view(), name='campaign-edit'),
    path('campaigns/<int:pk>/status/', views.RequestCampaignStatusUpdateView.as_view(), name='campaign-status'),
    path('campaigns/<int:pk>/manual-payments/add/', views.ManualPaymentCreateView.as_view(), name='campaign-manual-payment-add'),
    path('campaigns/<int:pk>/requests/<int:request_pk>/status/', views.ManualStimulusStatusUpdateView.as_view(), name='campaign-request-status'),
    path('campaigns/<int:pk>/approved-export/', views.CampaignApprovedRequestsExportView.as_view(), name='campaign-approved-export'),
    path('manual-payments/', views.ManualPaymentListView.as_view(), name='manual-payment-list'),
    path('manual-payments/add/', views.ManualPaymentCreateView.as_view(), name='manual-payment-add'),
    path('manual-payments/<int:pk>/edit/', views.ManualPaymentUpdateView.as_view(), name='manual-payment-edit'),
    path('manual-payments/<int:pk>/delete/', views.ManualPaymentDeleteView.as_view(), name='manual-payment-delete'),
]
