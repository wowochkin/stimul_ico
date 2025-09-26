from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import StimulusRequest
from .services import recompute_employee_totals


@receiver(post_save, sender=StimulusRequest)
def handle_request_save(sender, instance: StimulusRequest, **kwargs):
    recompute_employee_totals(instance.employee_id)


@receiver(post_delete, sender=StimulusRequest)
def handle_request_delete(sender, instance: StimulusRequest, **kwargs):
    recompute_employee_totals(instance.employee_id)
