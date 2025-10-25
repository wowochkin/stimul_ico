from django.contrib.auth.models import Group
from .models import UserDivision


def is_department_manager(user):
    """Проверяет, является ли пользователь руководителем департамента"""
    return user.groups.filter(name='Руководитель департамента').exists()


def is_employee(user):
    """Проверяет, является ли пользователь сотрудником"""
    return user.groups.filter(name='Сотрудник').exists()


def get_user_division(user):
    """Возвращает подразделение пользователя, если он руководитель департамента"""
    try:
        return user.user_division.division
    except UserDivision.DoesNotExist:
        return None


def can_view_all_requests(user):
    """Проверяет, может ли пользователь видеть все заявки"""
    return user.has_perm('stimuli.view_all_requests') or user.is_staff


def can_edit_request(user, request):
    """Проверяет, может ли пользователь редактировать конкретную заявку"""
    # Администраторы могут редактировать все
    if user.is_staff:
        return True
    
    # Руководители департамента могут редактировать заявки своего подразделения
    if is_department_manager(user):
        user_division = get_user_division(user)
        if user_division and request.employee.division == user_division:
            return True
    
    # Сотрудники могут редактировать только свои заявки в статусе "На рассмотрении"
    if is_employee(user) and request.requested_by == user:
        return request.status == request.Status.PENDING
    
    return False


def can_delete_request(user, request):
    """Проверяет, может ли пользователь удалить конкретную заявку"""
    # Администраторы могут удалять все
    if user.is_staff:
        return True
    
    # Руководители департамента могут удалять заявки своего подразделения
    if is_department_manager(user):
        user_division = get_user_division(user)
        if user_division and request.employee.division == user_division:
            return True
    
    # Сотрудники могут удалять только свои заявки в статусе "На рассмотрении"
    if is_employee(user) and request.requested_by == user:
        return request.status == request.Status.PENDING
    
    return False


def get_accessible_employees(user):
    """Возвращает queryset сотрудников, к которым у пользователя есть доступ"""
    from .models import Employee
    
    # Администраторы видят всех сотрудников
    if user.is_staff:
        return Employee.objects.all()
    
    # Руководители департамента видят сотрудников своего подразделения
    if is_department_manager(user):
        user_division = get_user_division(user)
        if user_division:
            return Employee.objects.filter(division=user_division)
    
    # Сотрудники видят только себя (поиск по имени пользователя)
    if is_employee(user):
        # Пытаемся найти сотрудника по имени пользователя
        try:
            return Employee.objects.filter(full_name__icontains=user.username)
        except Exception:
            return Employee.objects.none()
    
    return Employee.objects.none()
