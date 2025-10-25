from django.db.models import Q
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from one_time_payments.models import RequestCampaign
from stimuli.models import Employee, StimulusRequest

from .permissions import IsRequestOwnerOrAdmin
from .serializers import (
    EmployeeSerializer,
    RequestCampaignSerializer,
    StimulusRequestSerializer,
    UserProfileSerializer,
)


class EmployeeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Employee.objects.select_related('division', 'position')
        search = self.request.query_params.get('search')
        category = self.request.query_params.get('category')
        division = self.request.query_params.get('division')

        if search:
            queryset = queryset.filter(Q(full_name__icontains=search) | Q(justification__icontains=search))
        if category:
            queryset = queryset.filter(category=category)
        if division:
            queryset = queryset.filter(division_id=division)

        return queryset.order_by('full_name')


class StimulusRequestViewSet(viewsets.ModelViewSet):
    serializer_class = StimulusRequestSerializer
    permission_classes = [IsRequestOwnerOrAdmin]

    def get_queryset(self):
        queryset = StimulusRequest.objects.select_related(
            'employee',
            'employee__division',
            'employee__position',
            'requested_by',
            'campaign',
        )
        user = self.request.user
        if user.is_superuser or user.is_staff or user.has_perm('stimuli.view_all_requests'):
            return queryset
        return queryset.filter(requested_by=user)

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)

    def perform_update(self, serializer):
        user = self.request.user
        data = serializer.validated_data
        if not (user.is_superuser or user.is_staff or user.has_perm('stimuli.view_all_requests')):
            data.pop('status', None)
            data.pop('admin_comment', None)
        serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def statuses(self, request_obj):
        statuses = [{'value': value, 'label': label} for value, label in StimulusRequest.Status.choices]
        return Response(statuses)


class RequestCampaignViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RequestCampaignSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = RequestCampaign.objects.all()
        status_filter = self.request.query_params.get('status')
        
        if status_filter == 'active':
            return RequestCampaign.objects.active()
        
        # Ограничиваем выбор кампаний в зависимости от роли пользователя
        user = self.request.user
        if user.is_authenticated:
            from stimuli.permissions import is_employee, is_department_manager
            if is_employee(user) or is_department_manager(user):
                # Сотрудники и руководители департамента видят только открытые кампании
                queryset = queryset.filter(status='open')
            else:
                # Администраторы видят все кампании кроме черновиков
                queryset = queryset.exclude(status='draft')
        
        if status_filter:
            return queryset.filter(status=status_filter)
        return queryset


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profile_view(request):
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)
