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



def is_valid_qr(company, qr_code):
    interval = 180
    current_interval = int(time.time() // interval)

    # Geçerli interval için kodu oluştur
    valid_code = hashlib.sha256(f"{company.qr_secret}{current_interval}".encode()).hexdigest()

    # Bir önceki interval için de kontrol (zaman senkronizasyonu için)
    prev_code = hashlib.sha256(f"{company.qr_secret}{current_interval - 1}".encode()).hexdigest()

    return qr_code == valid_code or qr_code == prev_code



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_qr(request):
    qr_code = request.data.get('qr_code')
    if not qr_code:
        return Response({'error': 'QR kodu gerekli.'}, status=status.HTTP_400_BAD_REQUEST)

    # Tüm şirketleri tek tek kontrol etmek verimsiz oldu, ama simdilik kalsin:
    companies = Company.objects.all()
    matched_company = None
    for company in companies:
        if is_valid_qr(company, qr_code):
            matched_company = company
            break

    if not matched_company:
        return Response({'error': 'Geçersiz QR kodu.'}, status=status.HTTP_404_NOT_FOUND)

    user = request.user
    now = timezone.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    last_attendance = Attendance.objects.filter(
        user=user,
        company=matched_company,
        timestamp__gte=start_of_day
    ).order_by('-timestamp').first()

    action = 'exit' if last_attendance and last_attendance.action == 'entry' else 'entry'

    attendance = Attendance.objects.create(user=user, company=matched_company, action=action)

    return Response({
        'message': f'{action.capitalize()} kaydı başarıyla alındı.',
        'timestamp': attendance.timestamp,
        'company': matched_company.name,
        'action': attendance.action,
    })






class CompanyInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        company = user.company  # veya ilişkiye göre uyarlarsın
        return Response({
            "name": company.name,
            "qr_code": company.qr_code
        })
