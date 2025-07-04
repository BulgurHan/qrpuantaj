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


def is_valid_qr(company, qr_code):
    interval = 180
    current_interval = int(time.time() // interval)

    # Geçerli interval için kodu oluştur
    valid_code = hashlib.sha256(f"{company.qr_secret}{current_interval}".encode()).hexdigest()

    # Bir önceki interval için de kontrol (zaman senkronizasyonu için)
    prev_code = hashlib.sha256(f"{company.qr_secret}{current_interval - 1}".encode()).hexdigest()

    return qr_code == valid_code or qr_code == prev_code





logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_qr(request):
    try:
        qr_code = request.data.get('qr_code', '').strip()
        logger.info(f"QR tarama denemesi: {qr_code[:10]}...")  # Loglama
        
        if not qr_code:
            logger.warning("QR kodu boş gönderildi")
            return Response({'error': 'QR kodu gerekli.'}, status=status.HTTP_400_BAD_REQUEST)

        # Şirket kontrolünü optimize edelim
        matched_company = Company.objects.filter(
            qr_code__iexact=qr_code  # Büyük/küçük harf duyarsız
        ).first()

        if not matched_company:
            logger.warning(f"Eşleşen şirket bulunamadı: {qr_code[:10]}...")
            return Response(
                {'error': 'Geçersiz QR kodu. Lütfen geçerli bir şirket QR kodu tarayın.'},
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

        logger.info(f"Başarılı kayıt - Kullanıcı: {user}, Şirket: {matched_company}, İşlem: {action}")

        return Response({
            'message': f'{action.capitalize()} kaydı başarıyla alındı.',
            'timestamp': attendance.timestamp,
            'company': matched_company.name,
            'action': action,
            'qr_code': qr_code[:6] + '...'  # Güvenlik için kısmi gösterim
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
