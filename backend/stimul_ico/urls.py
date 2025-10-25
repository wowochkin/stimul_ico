from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.http import HttpResponse


# Супер-простой view для тестирования без middleware
def ultra_simple_test(request):
    """Максимально простой endpoint для диагностики"""
    return HttpResponse("OK", content_type='text/plain', status=200)


urlpatterns = [
    path('ultra-simple/', ultra_simple_test, name='ultra-simple'),
    path('health/', ultra_simple_test, name='health-simple'),  # Простой health check для Railway
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('api/', include(('api.urls', 'api'), namespace='api')),
    path('staffing/', include(('staffing.urls', 'staffing'), namespace='staffing')),
    path('recurring/', include(('recurring_payments.urls', 'recurring_payments'), namespace='recurring_payments')),
    path('one-time/', include(('one_time_payments.urls', 'one_time_payments'), namespace='one_time_payments')),
    path('budgeting/', include(('budgeting.urls', 'budgeting'), namespace='budgeting')),
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
    path('', include('stimuli.urls')),
]
