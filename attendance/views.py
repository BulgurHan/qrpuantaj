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
import json



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
    try:
        # Request body'nin JSON olduğundan emin ol
        try:
            data = json.loads(request.body)
            qr_code = data.get('qr_code')
        except json.JSONDecodeError:
            return Response({'error': 'Geçersiz JSON formatı'}, status=status.HTTP_400_BAD_REQUEST)

        if not qr_code:
            return Response({'error': 'QR kodu gerekli.'}, status=status.HTTP_400_BAD_REQUEST)

        # Veritabanı sorgusunu optimize et
        matched_company = Company.objects.filter(qr_code_prefix=qr_code[:5]).first()
        
        if not matched_company:
            return Response({'error': 'Geçersiz QR kodu.'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        now = timezone.now()
        
        # Son kaydı bul
        last_attendance = Attendance.objects.filter(
            user=user,
            company=matched_company,
            timestamp__date=now.date()
        ).order_by('-timestamp').first()

        action = 'exit' if last_attendance and last_attendance.action == 'entry' else 'entry'

        attendance = Attendance.objects.create(
            user=user,
            company=matched_company,
            action=action
        )

        return Response({
            'message': f'{action.capitalize()} kaydı başarıyla alındı.',
            'timestamp': attendance.timestamp.isoformat(),
            'company': matched_company.name,
            'action': attendance.action,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class CompanyInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        company = user.company  # veya ilişkiye göre uyarlarsın
        return Response({
            "name": company.name,
            "qr_code": company.qr_code
        })
