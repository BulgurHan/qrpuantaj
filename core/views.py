from django.shortcuts import render,redirect
from django.http import JsonResponse,HttpResponse
from .models import Company, QRToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta, date
import io
from django.shortcuts import get_object_or_404
from django.utils.timezone import make_aware
from django.db import transaction
import time
import hashlib
import qrcode
from io import BytesIO
import calendar
from collections import defaultdict
from django.utils.timezone import localtime
from django.contrib import messages
from users.forms import StaffForm   
from .forms import ManualAttendanceForm
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
    shifts = ShiftSession.objects.filter(user=user).order_by('date', 'start_time')
    
    now_date = timezone.now().date().strftime('%Y-%m-%d')  # Template'e göndereceğimiz
    
    daily_records = []
    for shift in shifts:
        record = {
            'date': shift.date.strftime('%Y-%m-%d'),
            'entry': shift.start_time.strftime('%H:%M:%S'),
            'exit': shift.end_time.strftime('%H:%M:%S') if shift.end_time else None,
            'is_overnight': shift.is_overnight,
            'status': 'complete' if shift.end_time else 'incomplete'
        }
        daily_records.append(record)

    context = {
        'daily_records': daily_records,
        'now_date': now_date  # Template'de kullanılacak
    }
    return render(request, 'attendances.html', context)


def calendar_summary(request):
    # Tarih ayarları
    bugun = timezone.localtime().date()
    yil = int(request.GET.get('yil', bugun.year))
    ay = int(request.GET.get('ay', bugun.month))
    
    # Kullanıcı ve şirket bilgisi
    kullanici = request.user
    sirket = kullanici.company
    gun_sayisi = calendar.monthrange(yil, ay)[1]
    
    # Takvim günlerini hazırla
    gunler = []
    for gun in range(1, gun_sayisi + 1):
        current_date = date(yil, ay, gun)
        
        # Vardiyaları getir
        vardiyalar = ShiftSession.objects.filter(
            user=kullanici,
            date=current_date
        )
        
        # Toplam çalışma süresi
        toplam_saat = sum(
            shift.duration.total_seconds() / 3600 
            for shift in vardiyalar 
            if shift.end_time
        )
        
        # Durum belirleme
        if toplam_saat == 0:
            durum = 'yok'
        elif toplam_saat >= sirket.daily_work_hours:
            durum = 'tam' if toplam_saat == sirket.daily_work_hours else 'fazla-mesai'
        else:
            durum = 'eksik'
        
        gunler.append({
            'tarih': current_date,
            'saat': round(toplam_saat, 2),
            'durum': durum,
            'vardiya_sayisi': vardiyalar.count(),
        })

    # Türkçe ay isimleri
    turkce_aylar = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    
    context = {
        'gunler': gunler,
        'yil': yil,
        'ay': ay,
        'ay_adi': turkce_aylar[ay],
        'onceki_ay': ay - 1 if ay > 1 else 12,
        'onceki_yil': yil - 1 if ay == 1 else yil,
        'sonraki_ay': ay + 1 if ay < 12 else 1,
        'sonraki_yil': yil + 1 if ay == 12 else yil,
        'gunluk_mesai': sirket.daily_work_hours,
    }
    return render(request, 'calender.html', context)




def daily_attendance_report(request):
    date_str = request.GET.get('date')
    if date_str:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        selected_date = timezone.now().date()

    company = request.user.company
    shifts = ShiftSession.objects.filter(
        company=company,
        date=selected_date  # Artık direkt tarih alanını kullanıyoruz
    ).select_related('user').order_by('user__first_name', 'start_time')

    rows = []
    for shift in shifts:
        # Süre hesaplama (gece vardiyaları dahil)
        if shift.end_time:
            duration = shift.duration.total_seconds() / 3600
            expected = shift.user.company.daily_work_hours
            if duration >= expected:
                status = '🕒 Fazla Mesai' if duration > expected else '✅ Tam Süre'
            else:
                status = '⚠️ Eksik Mesai'
        else:
            duration = 0
            status = '⏳ Devam Ediyor' if shift.start_time.date() == timezone.now().date() else '❌ Eksik Çıkış'

        rows.append({
            'user': shift.user.get_full_name(),
            'entry': shift.start_time.time().strftime('%H:%M'),
            'exit': shift.end_time.time().strftime('%H:%M') if shift.end_time else '-',
            'duration': round(duration, 2),
            'status': status,
            'is_overnight': shift.is_overnight  # Template'de özel stil için
        })

    return render(request, 'report.html', {
        'rows': rows,
        'selected_date': selected_date.strftime('%Y-%m-%d')
    })


def staff_list(request):
    company = request.user.company
    query = request.GET.get('q', '')

    users = User.objects.filter(company=company)
    if query:
        users = users.filter(first_name__icontains=query)

    return render(request, 'staff-list.html', {
        'users': users,
        'query': query
    })


def staff_create(request):
    if request.method == 'POST':
        form = StaffForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.company = request.user.company
            user.is_staff = False
            user.is_active = True
            user.save()
            messages.success(request, "Personel eklendi.")
            return redirect('staff_list')
    else:
        form = StaffForm()

    return render(request, 'staff-form.html', {'form': form, 'is_edit': False})


def staff_update(request, user_id):
    person = get_object_or_404(User, id=user_id, company=request.user.company)
    if request.method == 'POST':
        form = StaffForm(request.POST, instance=person)
        if form.is_valid():
            form.save()
            messages.success(request, "Personel güncellendi.")
            return redirect('staff_list')
    else:
        form = StaffForm(instance=person)

    return render(request, 'staff-form.html', {'form': form, 'is_edit': True, 'person': person})



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

def company_qr_code(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    qr_code_str = generate_dynamic_qr(company)

    context = {
        'company': company,
        'qr_code_str': qr_code_str,
    }
    return render(request, 'qr_code.html', context)

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
    now = timezone.now()  

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
        active_shift.end_time = now
        active_shift.save()
        Attendance.objects.create(user=user, company=company, action='exit', timestamp=now)
        return Response({'status': 'Çıkış yapıldı', 'ended_at': now})
    else:
        ShiftSession.objects.create(employee=employee, start_time=now)
        Attendance.objects.create(user=user, company=company, action='entry', timestamp=now)
        return Response({'status': 'Giriş yapıldı', 'started_at': now})


def manual_attendance_entry(request):
    if request.method == 'POST':
        form = ManualAttendanceForm(request.POST, request=request)
        if form.is_valid():
            cd = form.cleaned_data
            user     = cd['user']
            company  = request.user.company   # şirketi request'ten alıyoruz
            action   = cd['action']
            ts       = cd['timestamp']           # datetime‑local’den gelen değer
            date_only = ts.date()

            with transaction.atomic():
                # Aynı gün & aynı action için varsa kaydı çek
                att = Attendance.objects.filter(
                    user=user,
                    company=company,
                    action=action,
                    timestamp__date=date_only,     # ← gün bazında eşleşme
                    added_by_hr=True               # sadece manuel olanları hedefliyoruz
                ).first()

                if att:
                    att.timestamp = ts            # saat/dakika güncelle
                    att.save(update_fields=['timestamp'])
                    messages.success(request, "📝 Kayıt güncellendi ({} ⇒ {}).".format(action, ts.strftime('%H:%M')))
                else:
                    Attendance.objects.create(
                        user=user,
                        company=company,
                        action=action,
                        timestamp=ts,
                        added_by_hr=True
                    )
                    messages.success(request, "✔️ Yeni kayıt eklendi.")

            return redirect('manual_attendance_entry')
        else:
            messages.error(request, "❌ Lütfen formu kontrol edin.")
    else:
        form = ManualAttendanceForm(request=request)

    return render(request, 'manual_entry.html', {'form': form})
