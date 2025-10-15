from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='overview'),
    path('export/', views.DashboardExportView.as_view(), name='export'),
]
