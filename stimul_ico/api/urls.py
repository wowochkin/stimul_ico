from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from . import views

app_name = 'api'

router = DefaultRouter()
router.register('employees', views.EmployeeViewSet, basename='employee')
router.register('requests', views.StimulusRequestViewSet, basename='request')
router.register('campaigns', views.RequestCampaignViewSet, basename='campaign')

urlpatterns = [
    path('auth/token/', obtain_auth_token, name='token'),
    path('auth/profile/', views.profile_view, name='profile'),
    path('', include(router.urls)),
]
