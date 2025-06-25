from django.shortcuts import render
from django.http import JsonResponse,HttpResponse
from .models import Company, QRToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta, date
import io
from django.shortcuts import get_object_or_404
import time
import hashlib
import qrcode
from io import BytesIO
import calendar
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
    # URL parametrelerinden ay ve yıl al
    today = timezone.localtime().date()
    year = int(request.GET.get('yil', today.year))
    month = int(request.GET.get('ay', today.month))

    user = request.user
    gun_sayisi = calendar.monthrange(year, month)[1]

    days = []
    for gun in range(1, gun_sayisi + 1):
        current_date = date(year, month, gun)
        start = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))
        end = start + timedelta(days=1)

        logs = Attendance.objects.filter(user=user, timestamp__range=(start, end)).order_by('timestamp')
        total_hours = 0

        if logs.count() >= 2:
            for i in range(0, len(logs) - 1, 2):
                entry = logs[i]
                exit = logs[i + 1] if i + 1 < len(logs) else None
                if exit:
                    delta = exit.timestamp - entry.timestamp
                    total_hours += delta.total_seconds() / 3600

        if total_hours == 0:
            status = 'none'
        elif total_hours >= user.company.daily_working_hours:
            status = 'full' if total_hours == user.company.daily_working_hours else 'overtime'
        else:
            status = 'missing'

        days.append({
            'date': current_date,
            'hours': round(total_hours, 2),
            'status': status,
        })

    turkce_aylar = [
    "", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"
]
    ay_adi = turkce_aylar[month]

    context = {
        'days': days,
        'yil': year,
        'ay': month,
        'ay_adi': ay_adi,
        'onceki_ay': month - 1 if month > 1 else 12,
        'onceki_yil': year - 1 if month == 1 else year,
        'sonraki_ay': month + 1 if month < 12 else 1,
        'sonraki_yil': year + 1 if month == 12 else year,
    }
    return render(request, 'calender.html', context)



def daily_attendance_report(request):
    date_str = request.GET.get('date')
    if date_str:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        selected_date = timezone.now().date()

    company = request.user.company
    entries = Attendance.objects.filter(
        company=company,
        timestamp__date=selected_date
    ).order_by('user', 'timestamp')

    report = {}

    for entry in entries:
        user = entry.user
        if user not in report:
            report[user] = {'entry': None, 'exit': None}

        if entry.action == 'entry':
            report[user]['entry'] = entry.timestamp
        elif entry.action == 'exit':
            report[user]['exit'] = entry.timestamp

    rows = []
    for user, data in report.items():
        entry = data['entry']
        exit = data['exit']
        if entry and exit:
            duration = exit - entry
            hours = duration.total_seconds() / 3600
            expected = user.company.daily_work_hours  # örnek: 8.0 saat
            if hours >= expected:
                status = '🕒 Fazla Mesai' if hours > expected else '✅ Tam Süre'
            else:
                status = '⚠️ Eksik Mesai'
        else:
            hours = 0
            status = '❌ Eksik Kayıt'

        rows.append({
            'user': user.get_full_name(),
            'entry': entry.time().strftime('%H:%M') if entry else '-',
            'exit': exit.time().strftime('%H:%M') if exit else '-',
            'duration': round(hours, 2),
            'status': status,
            'date': selected_date
        })

    return render(request, 'report.html', {
        'rows': rows,
        'selected_date': selected_date.strftime('%Y-%m-%d')
    })


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

