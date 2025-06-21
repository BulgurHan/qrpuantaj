from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
import json
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = getattr(user, 'role', '')
        return token

    def validate(self, attrs):
        email = attrs.get('email')
        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError('Geçersiz e-posta veya şifre')
        attrs['username'] = user.username  # veya user.email
        return super().validate(attrs)

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


@csrf_exempt
def signin(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Yalnızca POST kabul edilir'}, status=405)
    
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
    except Exception:
        return JsonResponse({'error': 'Geçersiz JSON'}, status=400)
    
    if not email or not password:
        return JsonResponse({'error': 'E-posta ve şifre gerekli'}, status=400)
    
    user = authenticate(request, username=email, password=password)
    if user is None:
        return JsonResponse({'error': 'Geçersiz e-posta veya şifre'}, status=400)
    
    login(request, user)
    refresh = RefreshToken.for_user(user)
    return JsonResponse({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'message': 'Login başarılı'
    })