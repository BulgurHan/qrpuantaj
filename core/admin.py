from django.contrib import admin
from .models import Company, Branch, Department, Employee, ShiftSession, QRToken

admin.site.register(Company)
admin.site.register(Branch)
admin.site.register(Department)
admin.site.register(Employee)
admin.site.register(ShiftSession)
admin.site.register(QRToken)
