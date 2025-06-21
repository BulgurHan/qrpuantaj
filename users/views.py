from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import SignInForm
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


def signin(request):
    if request.method == 'POST':
        form = SignInForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    # Kullanıcıyı oturum açtır
                    login(request, user)
                    return redirect('home')
                else:
                    form.add_error(None, 'Parola yanlış.')
            except User.DoesNotExist:
                form.add_error(None, 'Kullanıcı bulunamadı.')
    else:
        form = SignInForm()
    return render(request, 'login.html', {'form': form})

