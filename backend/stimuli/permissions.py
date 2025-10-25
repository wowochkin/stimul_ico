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


def can_change_request_status(user, request_obj):
    """Проверяет, может ли пользователь изменять статус конкретной заявки"""
    # Администраторы могут изменять статус всех заявок
    if user.is_staff:
        return True
    
    # Руководители департамента НЕ могут изменять статус заявок
    # Сотрудники НЕ могут изменять статус заявок (даже своих)
    return False


def can_edit_request(user, request_obj):
    """Проверяет, может ли пользователь редактировать конкретную заявку"""
    # Администраторы могут редактировать все
    if user.is_staff:
        return True
    
    # Руководители департамента НЕ могут редактировать заявки
    # Сотрудники могут редактировать только свои заявки в статусе "На рассмотрении"
    if is_employee(user) and request_obj.requested_by == user:
        return request_obj.status == request_obj.Status.PENDING
    
    return False


def can_delete_request(user, request_obj):
    """Проверяет, может ли пользователь удалить конкретную заявку"""
    # Администраторы могут удалять все
    if user.is_staff:
        return True
    
    # Руководители департамента могут удалять только свои заявки в статусе "На рассмотрении"
    if is_department_manager(user) and request_obj.requested_by == user:
        return request_obj.status == request_obj.Status.PENDING
    
    # Сотрудники могут удалять только свои заявки в статусе "На рассмотрении"
    if is_employee(user) and request_obj.requested_by == user:
        return request_obj.status == request_obj.Status.PENDING
    
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
        return Employee.objects.none()
    
    # Сотрудники видят только себя
    if is_employee(user):
        try:
            return Employee.objects.filter(user=user)
        except Exception:
            return Employee.objects.none()
    
    return Employee.objects.none()
