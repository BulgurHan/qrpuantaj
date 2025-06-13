from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from core.models import Employee

@receiver(post_save, sender=User)
def create_employee(sender, instance, created, **kwargs):
    if created and instance.role == 'staff':
        Employee.objects.create(user=instance, department=None)  # veya default dept.
