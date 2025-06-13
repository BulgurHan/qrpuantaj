from django.urls import path
from .views import scan_qr, generate_qr_token

urlpatterns = [
    path('api/qr/generate/<int:company_id>/', generate_qr_token),
    path('api/qr/scan/', scan_qr),
]
