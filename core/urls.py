from django.urls import path
from .views import  generate_qr_token, qr_scan_api
from users.views import signin

urlpatterns = [
    path('api/qr/generate/<int:company_id>/', generate_qr_token),
    path('api/qr-scan/', qr_scan_api, name='qr_scan_api'),
    path('api/signin/', signin, name='signin'), 
]
