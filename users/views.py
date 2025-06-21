from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # İstersen role gibi ek bilgiler koy
        token['role'] = user.role
        return token

    def validate(self, attrs):
        # 'email' üzerinden doğrulama
        user = User.objects.get(email=attrs['email'])
        attrs['username'] = user.email
        return super().validate(attrs)

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
