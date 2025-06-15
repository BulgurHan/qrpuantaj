from django.urls import path
from .views import scan_qr

urlpatterns = [
    path('scan_qr/', scan_qr, name='scan_qr'),
]
