from django.http import JsonResponse
from .models import Company, QRToken
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import QRToken, ShiftSession, Employee, Company, User



def generate_qr_token(request, company_id):
    # → ileri aşamada sadece HR ya da owner olanlar bu endpoint'e erişebilmeli
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonResponse({'error': 'Company not found'}, status=404)

    token_obj = QRToken.generate_token(company)
    return JsonResponse({'token': token_obj.token})



@csrf_exempt
def scan_qr(request):
    token = request.GET.get('token')
    user_id = request.GET.get('user_id')  # bunu JWT tokenla yapacağız sonra

    if not token or not user_id:
        return JsonResponse({'error': 'Eksik veri'}, status=400)

    try:
        qr_token = QRToken.objects.get(token=token)
    except QRToken.DoesNotExist:
        return JsonResponse({'error': 'Geçersiz QR'}, status=404)

    if not qr_token.is_valid():
        return JsonResponse({'error': 'QR süresi dolmuş'}, status=400)

    try:
        user = User.objects.get(id=user_id)
        employee = Employee.objects.get(user=user)
    except (User.DoesNotExist, Employee.DoesNotExist):
        return JsonResponse({'error': 'Personel bulunamadı'}, status=404)

    now = timezone.now()

    # Son vardiyaya bak
    last_session = ShiftSession.objects.filter(employee=employee).order_by('-start_time').first()

    if not last_session or last_session.end_time:
        # Yeni mesai başlat
        ShiftSession.objects.create(employee=employee, start_time=now)
        return JsonResponse({'status': 'Mesai Başladı'})
    else:
        # Mesaiyi bitir
        last_session.end_time = now
        last_session.save()
        return JsonResponse({'status': 'Mesai Bitti'})
