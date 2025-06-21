from django.shortcuts import render
from django.http import JsonResponse,HttpResponse
from .models import Company, QRToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
import io
from django.shortcuts import get_object_or_404
import time
import hashlib
import qrcode
from io import BytesIO
from .models import QRToken, ShiftSession, Employee, Company, User, Attendance


def home(request):
    context = dict()
    return render(request,'home.html',context)


def qr_scan(request):
    context = dict()
    return render(request, 'qr_scan.html', context)


def generate_dynamic_qr(company):
    # Örnek: şirketin gizli anahtarı + 3 dakikalık zaman dilimi
    interval = 180  # saniye
    current_interval = int(time.time() // interval)
    data = f"{company.qr_secret}{current_interval}"
    qr_code_str = hashlib.sha256(data.encode()).hexdigest()
    return qr_code_str

def qr_code_image(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    qr_code_str = generate_dynamic_qr(company)

    qr = qrcode.make(qr_code_str)

    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    buf.seek(0)

    return HttpResponse(buf, content_type='image/png')



def company_qr_code(request, company_id):
    company = Company.objects.get(id=company_id)
    company.update_qr_code()  # Güncel qr kodunu hesapla ve kaydet

    qr_img = qrcode.make(company.qr_code)

    buffer = BytesIO()
    qr_img.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()

    return HttpResponse(img_bytes, content_type='image/png')



def generate_qr_token(request, company_id):
    # → ileri aşamada sadece HR ya da owner olanlar bu endpoint'e erişebilmeli
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonResponse({'error': 'Company not found'}, status=404)

    token_obj = QRToken.generate_token(company)
    return JsonResponse({'token': token_obj.token})



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def qr_scan_api(request):
    qr_code = request.data.get('qr_code')
    user = request.user

    if not qr_code:
        return Response({'error': 'QR kod gerekli'}, status=400)

    try:
        company = Company.objects.get(qr_code=qr_code)
    except Company.DoesNotExist:
        return Response({'error': 'Geçersiz QR kodu'}, status=404)

    try:
        employee = Employee.objects.get(user=user)
    except Employee.DoesNotExist:
        return Response({'error': 'Bu kullanıcı sisteme personel olarak tanımlı değil.'}, status=403)

    # Çıkış mı yapıyoruz yoksa giriş mi?
    active_shift = ShiftSession.objects.filter(employee=employee, end_time__isnull=True).last()

    if active_shift:
        active_shift.end_time = timezone.now()
        active_shift.save()
        Attendance.objects.create(user=user, company=company, action='exit')
        return Response({'status': 'Çıkış yapıldı', 'ended_at': active_shift.end_time})
    else:
        ShiftSession.objects.create(employee=employee, start_time=timezone.now())
        Attendance.objects.create(user=user, company=company, action='entry')
        return Response({'status': 'Giriş yapıldı', 'started_at': timezone.now()})

