from django.contrib import admin
from .models import Company, Branch, Department, Employee, ShiftSession, QRToken, Attendance,LeaveRequest,WorkSchedule

admin.site.register(Company)
admin.site.register(Branch)
admin.site.register(Department)
admin.site.register(Employee)
admin.site.register(QRToken)
admin.site.register(Attendance)
admin.site.register(LeaveRequest)
admin.site.register(WorkSchedule)

@admin.register(ShiftSession)
class ShiftSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'start_time', 'end_time', 'is_overnight', 'duration_hours')
    list_filter = ('is_overnight', 'date', 'company')
    search_fields = ('user__username', 'notes')
    readonly_fields = ('duration',)
