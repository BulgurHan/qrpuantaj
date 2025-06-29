from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import UserManager



# Kullanıcı rolleri ve şirket/şube ilişkilerini içeren genişletilmiş kullanıcı modeli
class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    ROLE_CHOICES = (
        ('company_owner', 'Company Owner'),
        ('hr', 'HR Manager'),
        ('staff', 'Staff'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    company = models.ForeignKey('core.Company', on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey('core.Branch', on_delete=models.SET_NULL, null=True, blank=True)

    objects = UserManager()  

    def __str__(self):
        return self.first_name + ' ' + self.last_name if self.first_name and self.last_name else self.email
