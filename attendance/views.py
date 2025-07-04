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

logger = logging.getLogger(__name__)

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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_qr(request):
    try:
        qr_code = request.data.get('qr_code', '').strip()
        logger.info(f"QR tarama denemesi: {qr_code[:10]}...")
        
        if not qr_code:
            logger.warning("QR kodu boş gönderildi")
            return Response(
                {'error': 'QR kodu gerekli.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Tüm şirketlerde geçerli QR kodunu ara
        matched_company = None
        for company in Company.objects.all():
            if is_valid_qr(company, qr_code):
                matched_company = company
                break

        if not matched_company:
            logger.warning(f"Geçersiz QR kodu: {qr_code[:10]}...")
            return Response(
                {'error': 'Geçersiz QR kodu veya süresi dolmuş. Lütfen yeni bir QR kodu tarayın.'},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user
        now = timezone.now()
        today = now.date()

        # Son kaydı bul
        last_attendance = Attendance.objects.filter(
            user=user,
            company=matched_company,
            timestamp__date=today
        ).order_by('-timestamp').first()

        action = 'exit' if last_attendance and last_attendance.action == 'entry' else 'entry'

        # Yeni kayıt oluştur
        attendance = Attendance.objects.create(
            user=user,
            company=matched_company,
            action=action
        )

        logger.info(
            f"Başarılı kayıt - Kullanıcı: {user.id}, "
            f"Şirket: {matched_company.id}, "
            f"İşlem: {action}"
        )

        return Response({
            'message': f'{action.capitalize()} kaydı başarıyla alındı.',
            'timestamp': attendance.timestamp,
            'company': matched_company.name,
            'action': action,
            'next_interval': int((time.time() // 180) + 1) * 180  # Sonraki yenileme zamanı
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"QR tarama hatası: {str(e)}", exc_info=True)
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
