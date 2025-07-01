# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction
from .models import Attendance, ShiftSession  


@receiver(post_save, sender=Attendance)
def handle_shift_automation(sender, instance, created, **kwargs):
    """
    Attendance kayıtlarını otomatik olarak ShiftSession'a dönüştürür
    """
    with transaction.atomic():
        user = instance.user
        timestamp = instance.timestamp
        
        # Açık vardiyayı bul
        active_shift = ShiftSession.objects.filter(
            user=user,
            end_time__isnull=True
        ).first()

        if instance.action == 'entry':
            if active_shift:
                # Var olan vardiyayı güncelle
                active_shift.start_time = timestamp
                active_shift.save(update_fields=['start_time'])
            else:
                # Yeni vardiya oluştur
                ShiftSession.objects.create(
                    user=user,
                    company=instance.company,
                    start_time=timestamp,
                    date=timestamp.date()
                )

        elif instance.action == 'exit' and active_shift:
            # Gece vardiyası kontrolü
            is_overnight = timestamp.date() > active_shift.date
            
            active_shift.end_time = timestamp
            active_shift.is_overnight = is_overnight
            active_shift.save(update_fields=['end_time', 'is_overnight'])