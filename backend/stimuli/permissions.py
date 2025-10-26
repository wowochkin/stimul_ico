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
        user_division_obj = user.user_division
        # Если установлен флаг "доступ ко всем сотрудникам", возвращаем None (все сотрудники)
        if user_division_obj.can_view_all:
            return None
        return user_division_obj.division
    except UserDivision.DoesNotExist:
        return None


def can_view_all_requests(user):
    """Проверяет, может ли пользователь видеть все заявки"""
    # Администраторы видят все заявки
    if user.is_staff:
        return True
    
    # Проверяем право видеть все заявки
    if user.has_perm('stimuli.view_all_requests'):
        return True
    
    # Руководители департамента с флагом can_view_all видят все заявки
    if is_department_manager(user):
        try:
            return user.user_division.can_view_all
        except UserDivision.DoesNotExist:
            return False
    
    return False


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
    
    # Руководители департамента видят сотрудников своего подразделения или всех, если есть право can_view_all
    if is_department_manager(user):
        try:
            user_division_obj = user.user_division
            # Если установлен флаг "доступ ко всем сотрудникам"
            if user_division_obj.can_view_all:
                return Employee.objects.all()
            # Иначе видит только сотрудников своего подразделения
            user_division = user_division_obj.division
            if user_division:
                return Employee.objects.filter(division=user_division)
        except UserDivision.DoesNotExist:
            pass
        return Employee.objects.none()
    
    # Сотрудники видят только себя
    if is_employee(user):
        try:
            return Employee.objects.filter(user=user)
        except Exception:
            return Employee.objects.none()
    
    return Employee.objects.none()
