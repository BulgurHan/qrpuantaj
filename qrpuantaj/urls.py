from django.contrib import admin
from django.views.generic import TemplateView
from django.urls import path,include
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from core.views import qr_code_image,home,qr_scan,login_view,attendances, calendar_summary, daily_attendance_report,staff_list, staff_create,staff_update,company_qr_code, manual_attendance_entry, employee_monthly_report,leave_request_create,leave_approval_list,leave_approve, ScheduleCreateView, EmployeeScheduleView
from users.views import MyTokenObtainPairView 


urlpatterns = [
    path('admin/', admin.site.urls),
    path('core/', include('core.urls')),
    path('api/', include('attendance.urls')),
    path('', home, name='home'),
    path('qr-scan/', qr_scan, name='qr_scan'),
    path('login/', login_view, name='login_view'),
    path('company/<int:company_id>/qr_image/', qr_code_image, name='qr_code_image'),
    path('attendances/', attendances, name='attendances'),
    path('calendar-summary/', calendar_summary, name='calendar_summary'),
    path('daily-attendance-report/', daily_attendance_report, name='daily_attendance_report'), 
    path('monthly-report/', employee_monthly_report, name='employee_monthly_report'),
    path('staff/', staff_list, name='staff_list'),
    path('staff/add/', staff_create, name='staff_create'),
    path('staff/<int:user_id>/edit/', staff_update, name='staff_update'),
    path('qr/<int:company_id>/', company_qr_code, name='company_qr_code'),
    path('attendance/add/', manual_attendance_entry, name='manual_attendance_entry'),
    path('leave-request-create/', leave_request_create, name='leave_request_create'),
    path('leave-approval-list/', leave_approval_list, name='leave_approval_list'),
    path('leave-approve/<int:pk>/', leave_approve, name='leave_approve'),
    path('schedule/create/', ScheduleCreateView.as_view(), name='create_schedule'),
    path('my-schedule/', EmployeeScheduleView.as_view(), name='employee_schedule'),
    path('test/', TemplateView.as_view(template_name='test.html'), name='test'),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]
