from django.db import models
from django.utils import timezone
from users.models import User  # Kullanıcı modelini içe aktar
import uuid



class Company(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    package = models.CharField(max_length=50)  # Basic, Pro vs.
    qr_secret = models.UUIDField(default=uuid.uuid4)  # QR token hashleme için gizli anahtar

class Branch(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

class Department(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)

class ShiftSession(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    auto_closed = models.BooleanField(default=False)  # unutulan çıkışlar için

class QRToken(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return self.expires_at > timezone.now()
