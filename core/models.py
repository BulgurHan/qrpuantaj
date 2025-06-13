from django.db import models
from django.utils import timezone
from datetime import timedelta
from users.models import User  # Kullanıcı modelini içe aktar
import uuid



class Company(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    package = models.CharField(max_length=50)  # Basic, Pro vs.
    qr_secret = models.UUIDField(default=uuid.uuid4)  # QR token hashleme için gizli anahtar
    def __str__(self):
        return self.name

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
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    auto_closed = models.BooleanField(default=False)  # unutulan çıkışlar için



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

