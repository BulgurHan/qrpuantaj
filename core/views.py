from django.shortcuts import render
from django.http import JsonResponse,HttpResponse
from .models import Company, QRToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
import io
from django.shortcuts import get_object_or_404
import time
import hashlib
import qrcode
from io import BytesIO
from collections import defaultdict
from django.utils.timezone import localtime
from .models import QRToken, ShiftSession, Employee, Company, User, Attendance


def home(request):
    context = dict()
    return render(request,'home.html',context)


def qr_scan(request):
    context = dict()
    return render(request, 'qr_scan.html', context)

def login_view(request):
    return render(request, 'login.html')


def attendances(request):
    user = request.user
    attendances = Attendance.objects.filter(user=user).order_by('timestamp')

    daily_records = defaultdict(dict)

    for att in attendances:
        date_str = localtime(att.timestamp).date().strftime('%Y-%m-%d')
        if att.action == 'entry':
            daily_records[date_str]['entry'] = localtime(att.timestamp).strftime('%H:%M:%S')
        elif att.action == 'exit':
            daily_records[date_str]['exit'] = localtime(att.timestamp).strftime('%H:%M:%S')

    context = {
        'daily_records': daily_records.items(),  # list of tuples: (date, {'entry': ..., 'exit': ...})
    }
    return render(request, 'attendances.html', context)


def calendar_summary(request):
    user = request.user
    today = timezone.now().date()
    gun_sayisi = 30  # son 30 gün

    days = []
    for i in range(gun_sayisi):
        date = today - timedelta(days=i)
        start = timezone.datetime.combine(date, timezone.datetime.min.time()).replace(tzinfo=timezone.get_current_timezone())
        end = start + timedelta(days=1)

        day_logs = Attendance.objects.filter(user=user, timestamp__range=(start, end)).order_by('timestamp')
        total_hours = 0

        if day_logs.count() >= 2:
            # Giriş/çıkış saatleri çift çift giderse hesapla
            for j in range(0, len(day_logs)-1, 2):
                entry = day_logs[j]
                exit = day_logs[j+1] if j+1 < len(day_logs) else None
                if exit:
                    delta = exit.timestamp - entry.timestamp
                    total_hours += delta.total_seconds() / 3600

        # Günlük statü belirle
        if total_hours == 0:
            status = 'none'
        elif total_hours >= user.company.daily_working_hours:
            status = 'full' if total_hours == user.company.daily_working_hours else 'overtime'
        else:
            status = 'missing'

        days.append({
            'date': date,
            'hours': round(total_hours, 2),
            'status': status,
        })

    context = {'days': days}
    return render(request, 'calender.html', context)


def generate_dynamic_qr(company):
    interval = 180  # 3 dakikalık zaman dilimi (saniye)
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

