from django.urls import path

from . import views

app_name = 'staffing'

urlpatterns = [
    path('quotas/', views.PositionQuotaListView.as_view(), name='quota-list'),
    path('quotas/create/', views.PositionQuotaCreateView.as_view(), name='quota-create'),
    path('quotas/<int:pk>/edit/', views.PositionQuotaUpdateView.as_view(), name='quota-edit'),
    path('quotas/<int:pk>/delete/', views.PositionQuotaDeleteView.as_view(), name='quota-delete'),
    path('quotas/<int:pk>/versions/create/', views.PositionQuotaVersionCreateView.as_view(), name='quota-version-create'),
    path('quotas/export/', views.PositionQuotaExportView.as_view(), name='quota-export'),
]
