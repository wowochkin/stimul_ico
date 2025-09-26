from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from stimuli.models import Employee, StimulusRequest


class Command(BaseCommand):
    help = 'Создать/обновить роли и базовые права для администраторов и ответственных.'

    def handle(self, *args, **options):
        employee_ct = ContentType.objects.get_for_model(Employee)
        request_ct = ContentType.objects.get_for_model(StimulusRequest)

        responsible_perms = Permission.objects.filter(
            content_type__in=[employee_ct, request_ct],
            codename__in=[
                'view_stimulusrequest',
                'add_stimulusrequest',
                'edit_pending_requests',
            ],
        )

        administrators_perms = Permission.objects.filter(
            content_type__in=[employee_ct, request_ct],
            codename__in=[
                'view_employee', 'add_employee', 'change_employee', 'delete_employee',
                'view_stimulusrequest', 'add_stimulusrequest', 'change_stimulusrequest', 'delete_stimulusrequest',
                'edit_pending_requests',
                'view_all_requests',
            ],
        )

        responsible_group, _ = Group.objects.get_or_create(name='Ответственные')
        responsible_group.permissions.set(responsible_perms)
        responsible_group.save()

        admins_group, _ = Group.objects.get_or_create(name='Администраторы')
        admins_group.permissions.set(administrators_perms)
        admins_group.save()

        self.stdout.write(self.style.SUCCESS('Роли обновлены: Администраторы, Ответственные.'))
