from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from core.models import Company, Attendance
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
import time
import hashlib
import logging
from django.core.exceptions import ValidationError


def is_valid_qr(company, qr_code):
    """
    Dinamik QR kod doğrulama fonksiyonu
    Her 180 saniyede (3 dakika) bir değişen kod üretir
    """
    interval = 180  # 3 dakika (saniye cinsinden)
    current_interval = int(time.time() // interval)

    # Geçerli ve bir önceki interval için kodları oluştur
    intervals_to_check = [current_interval, current_interval - 1]
    
    for interval_val in intervals_to_check:
        # Şirketin secret'ı ve interval değeri ile hash oluştur
        code_to_check = hashlib.sha256(
            f"{company.qr_secret}{interval_val}".encode()
        ).hexdigest()
        
        if qr_code == code_to_check:
            return True
    
    return False

logger = logging.getLogger(__name__)

def validate_timestamp(timestamp):
    """Timestamp validasyonu"""
    if timestamp > timezone.now():
        raise ValidationError("Gelecek tarihli kayıt oluşturulamaz")
    if timestamp < timezone.now() - timedelta(days=30):
        raise ValidationError("30 günden eski kayıt oluşturulamaz")

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_qr(request):
    """
    QR kod tarama ve devam kaydı oluşturma endpointi
    Kullanım:
    {
        "qr_code": "ABC123",
        "timestamp": "2023-07-20T14:30:00+03:00" # Opsiyonel
    }
    """
    try:
        # 1. Giriş verilerini al ve validasyon yap
        qr_code = request.data.get('qr_code', '').strip()
        timestamp = request.data.get('timestamp')
        
        if not qr_code:
            logger.warning("Boş QR kodu gönderildi")
            return Response(
                {'error': 'QR kodu gereklidir'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. QR kodunu şirketlerde ara
        matched_company = None
        for company in Company.objects.all():
            if is_valid_qr(company, qr_code):
                matched_company = company
                logger.info(f"QR kodu eşleşti: {company.name}")
                break

        if not matched_company:
            logger.warning(f"Geçersiz QR kodu: {qr_code[:8]}...")
            return Response(
                {'error': 'Geçersiz QR kodu. Lütfen geçerli bir şirket QR kodu tarayın.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. Timestamp ayarla (manuel veya otomatik)
        if timestamp:
            try:
                timestamp = timezone.datetime.fromisoformat(timestamp)
                validate_timestamp(timestamp)
            except (ValueError, ValidationError) as e:
                logger.error(f"Geçersiz timestamp: {timestamp}")
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            timestamp = timezone.now()

        # 4. Giriş/Çıkış durumunu belirle
        user = request.user
        today = timestamp.date()
        
        last_attendance = Attendance.objects.filter(
            user=user,
            company=matched_company,
            timestamp__date=today
        ).order_by('-timestamp').first()

        action = 'exit' if last_attendance and last_attendance.action == 'entry' else 'entry'

        # 5. Kaydı oluştur
        attendance = Attendance(
            user=user,
            company=matched_company,
            action=action,
            timestamp=timestamp
        )
        
        attendance.full_clean()  # Model validasyonu
        attendance.save()

        # 6. Başarılı yanıt
        response_data = {
            'message': f'{action.capitalize()} kaydı başarıyla oluşturuldu',
            'data': {
                'id': attendance.id,
                'user': user.username,
                'company': matched_company.name,
                'action': action,
                'timestamp': attendance.timestamp.isoformat(),
                'next_scan_allowed_after': (timestamp + timedelta(minutes=1)).isoformat()
            }
        }
        
        logger.info(f"Kayıt oluşturuldu: {response_data}")
        return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.exception("Beklenmeyen hata oluştu")
        return Response(
            {'error': 'Bir sunucu hatası oluştu. Lütfen tekrar deneyin.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



class CompanyInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        company = user.company  # veya ilişkiye göre uyarlarsın
        return Response({
            "name": company.name,
            "qr_code": company.qr_code
        })
