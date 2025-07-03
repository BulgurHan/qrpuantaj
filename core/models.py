from django.db import models
from django.utils import timezone
from datetime import timedelta
from users.models import User  
from django.contrib.auth import get_user_model
import uuid


User = get_user_model()

class Company(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    package = models.CharField(max_length=50)  # Basic, Pro vs.
    qr_secret = models.UUIDField(default=uuid.uuid4)  # QR token için gizli anahtar
    qr_code = models.CharField(max_length=255, unique=True, blank=True)  # Güncel QR string
    daily_work_hours = models.DecimalField(max_digits=4, decimal_places=2, default=8.00)

    def __str__(self):
        return self.name

    def generate_qr_code(self):
        # Mesela burada qr_secret ve timestamp ile unique bir kod üretelim
        import hashlib, time
        now = int(time.time() // 180)  # Her 3 dakikada 1 değişecek (180 sn)
        data = f"{self.qr_secret}-{now}"
        qr_hash = hashlib.sha256(data.encode()).hexdigest()
        return qr_hash

    def update_qr_code(self):
        self.qr_code = self.generate_qr_code()
        self.save(update_fields=['qr_code'])


class Branch(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    def __str__(self):
        return f"{self.name} - {self.company.name}"


class Department(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    def __str__(self):
        return f"{self.name} - {self.branch.name} ({self.branch.company.name})"


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)


class ShiftSession(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='shift_sessions',
        verbose_name='Kullanıcı'
    )
    company = models.ForeignKey(
        'Company',  # Company modelinizin adı
        on_delete=models.CASCADE,
        verbose_name='Şirket'
    )
    start_time = models.DateTimeField(
        verbose_name='Başlangıç Saati'
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Bitiş Saati'
    )
    date = models.DateField(
        verbose_name='Vardiya Tarihi',
        help_text='Vardiyanın başladığı tarih (16:00-00:30 gibi durumlar için)'
    )
    is_overnight = models.BooleanField(
        default=False,
        verbose_name='Gece Vardiyası',
        help_text='Ertesi güne sarkan vardiyalar için'
    )
    auto_closed = models.BooleanField(
        default=False,
        verbose_name='Otomatik Kapatıldı',
        help_text='Sistem tarafından kapatılan vardiyalar'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notlar'
    )

    class Meta:
        verbose_name = 'Vardiya Kaydı'
        verbose_name_plural = 'Vardiya Kayıtları'
        ordering = ['-date', '-start_time']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['is_overnight']),
        ]

    def __str__(self):
        status = "Açık" if self.end_time is None else "Kapalı"
        return f"{self.user} - {self.date} | {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M') if self.end_time else 'Devam Ediyor'} ({status})"

    @property
    def duration(self):
        """Toplam çalışma süresini hesaplar"""
        end = self.end_time or timezone.now()
        return end - self.start_time

    @property
    def duration_hours(self):
        """Süreyi saat olarak döner (örn: 8.5)"""
        return round(self.duration.total_seconds() / 3600, 2)

    def close_shift(self, end_time=None):
        """Vardiyayı manuel kapatma metodu"""
        self.end_time = end_time or timezone.now()
        
        # Gece vardiyası kontrolü
        if self.end_time.date() > self.date:
            self.is_overnight = True
            
        self.save(update_fields=['end_time', 'is_overnight'])



class QRToken(models.Model):
    company = models.OneToOneField('Company', on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        # 3 dakika geçerli
        return timezone.now() < self.created_at + timedelta(minutes=3)

    def __str__(self):
        return f"{self.company.name} - {self.token}"

    @staticmethod
    def generate_token(company):
        # Eski token varsa sil
        QRToken.objects.filter(company=company).delete()
        token = uuid.uuid4().hex
        return QRToken.objects.create(company=company, token=token)



class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(editable=True)
    action = models.CharField(max_length=10, choices=[('entry', 'Entry'), ('exit', 'Exit')])
    added_by_hr = models.BooleanField(default=False)  # Manuel mi eklendi?

    def __str__(self):
        return f"{self.user} - {self.company.name} - {self.action} @ {self.timestamp}"


class MonthlyReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    year = models.IntegerField()
    month = models.IntegerField()
    total_hours = models.FloatField(default=0)
    overtime_hours = models.FloatField(default=0)
    missing_hours = models.FloatField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Onay Bekliyor'),
        ('approved', 'Onaylandı'),
        ('rejected', 'Reddedildi')
    ])
    
    class Meta:
        unique_together = ('user', 'company', 'year', 'month')