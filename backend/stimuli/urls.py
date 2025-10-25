from django.urls import path
from django.http import HttpResponse

from . import views

# Супер-простой view для тестирования
def simple_test(request):
    return HttpResponse("OK - Simple test works!", content_type='text/plain')

urlpatterns = [
    path('', views.HomeRedirectView.as_view(), name='home'),
    path('simple/', simple_test, name='simple'),
    path('test/', views.TestView.as_view(), name='test'),
    path('employees/', views.EmployeeListView.as_view(), name='employee-list'),
    path('employees/add/', views.EmployeeCreateView.as_view(), name='employee-add'),
    path('employees/<int:pk>/edit/', views.EmployeeUpdateView.as_view(), name='employee-edit'),
    path('employees/<int:pk>/delete/', views.EmployeeDeleteView.as_view(), name='employee-delete'),
    path('employees/excel-template/', views.EmployeeExcelTemplateView.as_view(), name='employee-excel-template'),
    path('employees/excel-upload/', views.EmployeeExcelUploadView.as_view(), name='employee-excel-upload'),
    path('requests/', views.StimulusRequestListView.as_view(), name='request-list'),
    path('requests/new/', views.StimulusRequestCreateView.as_view(), name='request-create'),
    path('requests/bulk-create/', views.StimulusRequestBulkCreateView.as_view(), name='request-bulk-create'),
    path('requests/<int:pk>/edit/', views.StimulusRequestUpdateView.as_view(), name='request-edit'),
    path('requests/<int:pk>/update-status/', views.StimulusRequestStatusUpdateView.as_view(), name='request-status-update'),
    path('requests/<int:pk>/delete/', views.StimulusRequestDeleteView.as_view(), name='request-delete'),
    path('requests/bulk-delete/', views.StimulusRequestBulkDeleteView.as_view(), name='request-bulk-delete'),
]
