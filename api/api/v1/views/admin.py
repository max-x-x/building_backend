from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count

from api.models.object import ConstructionObject, ObjectStatus
from api.models.prescription import Prescription
from api.models.delivery import Delivery
from api.models.user import Roles


class AdminStatsView(APIView):
    """
    GET /api/v1/admin/stats
    Статистика для админа: объекты в работе, открытые нарушения, все поставки.
    Доступно только для роли ADMIN.
    """
    
    def get(self, request):
        # Проверяем права доступа
        if request.user.role != Roles.ADMIN:
            return Response({"detail": "Forbidden"}, status=403)
        
        # 1. Объекты в работе (все кроме завершенных и без ССК)
        objects_in_work = ConstructionObject.objects.filter(
            ~Q(status=ObjectStatus.COMPLETED),  # не завершенные
            ssk__isnull=False  # с назначенным ССК
        ).count()
        
        # 2. Открытые нарушения по всем объектам
        open_violations = Prescription.objects.filter(
            status="open"
        ).count()
        
        # 3. Все поставки по всем объектам (любой статус)
        total_deliveries = Delivery.objects.count()
        
        return Response({
            "objects_in_work": objects_in_work,
            "open_violations": open_violations,
            "total_deliveries": total_deliveries
        }, status=200)
