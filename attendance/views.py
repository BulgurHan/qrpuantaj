from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from core.models import Company, Attendance
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_qr(request):
    qr_data = request.data.get('qr_data')

    if not qr_data:
        return Response({'error': 'QR verisi gerekli.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        company = Company.objects.get(qr_code=qr_data)
    except Company.DoesNotExist:
        return Response({'error': 'Geçersiz QR kodu.'}, status=status.HTTP_404_NOT_FOUND)

    user = request.user
    now = timezone.now()

    # Aynı gün içinde kullanıcının son hareketini bul
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_attendance = Attendance.objects.filter(user=user, company=company, timestamp__gte=start_of_day).order_by('-timestamp').first()

    if last_attendance and last_attendance.action == 'entry':
        action = 'exit'
    else:
        action = 'entry'

    attendance = Attendance.objects.create(user=user, company=company, action=action)

    return Response({
        'message': f'{action.capitalize()} kaydı başarıyla alındı.',
        'timestamp': attendance.timestamp,
        'company': company.name,
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
