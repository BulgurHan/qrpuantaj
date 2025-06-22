from django.urls import path
from .views import scan_qr, CompanyInfoView

urlpatterns = [
    path('scan-qr/', scan_qr, name='scan_qr'),
    path('company-info/', CompanyInfoView.as_view()),
]
