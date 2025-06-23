"""
URL configuration for qrpuantaj project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.views.generic import TemplateView
from django.urls import path,include
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from core.views import qr_code_image,home,qr_scan,login_view,attendances
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
    path('test/', TemplateView.as_view(template_name='test.html'), name='test'),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]
