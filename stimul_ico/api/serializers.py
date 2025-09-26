from django.contrib.auth import get_user_model
from rest_framework import serializers

from one_time_payments.models import RequestCampaign
from stimuli.models import Employee, StimulusRequest

User = get_user_model()


class EmployeeSerializer(serializers.ModelSerializer):
    division_name = serializers.CharField(source='division.name', read_only=True)
    position_name = serializers.CharField(source='position.name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    salary_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    assignments_salary_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    allowance_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_payments = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id',
            'full_name',
            'division',
            'division_name',
            'position',
            'position_name',
            'category',
            'category_display',
            'rate',
            'allowance_amount',
            'allowance_reason',
            'allowance_until',
            'payment',
            'justification',
            'salary_amount',
            'assignments_salary_amount',
            'allowance_total',
            'total_payments',
        ]
        read_only_fields = [
            'division_name',
            'position_name',
            'category_display',
            'salary_amount',
            'assignments_salary_amount',
            'allowance_total',
            'total_payments',
        ]


class StimulusRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    requested_by_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    is_editable = serializers.SerializerMethodField()

    class Meta:
        model = StimulusRequest
        fields = [
            'id',
            'employee',
            'employee_name',
            'campaign',
            'campaign_name',
            'amount',
            'justification',
            'status',
            'status_display',
            'admin_comment',
            'requested_by',
            'requested_by_name',
            'created_at',
            'updated_at',
            'is_editable',
        ]
        read_only_fields = [
            'requested_by',
            'requested_by_name',
            'status_display',
            'created_at',
            'updated_at',
            'employee_name',
            'campaign_name',
            'is_editable',
        ]

    def get_requested_by_name(self, obj):
        full_name = obj.requested_by.get_full_name()
        return full_name or obj.requested_by.get_username()

    def get_is_editable(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if request.user.has_perm('stimuli.view_all_requests') or request.user.is_staff or request.user.is_superuser:
            return True
        return obj.requested_by_id == request.user.id and obj.status == StimulusRequest.Status.PENDING

    def validate_employee(self, value):
        if not value:
            raise serializers.ValidationError('Сотрудник обязателен.')
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Сумма должна быть положительной.')
        return value


class RequestCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestCampaign
        fields = [
            'id',
            'name',
            'status',
            'opens_at',
            'deadline',
            'auto_close_day',
            'auto_close_enabled',
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email', 'is_staff', 'groups']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.get_username()

    def get_groups(self, obj):
        return list(obj.groups.values_list('name', flat=True))
