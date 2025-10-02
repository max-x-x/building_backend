from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q

from api.models.object import ConstructionObject, ObjectStatus
from api.models.prescription import Prescription
from api.models.delivery import Delivery
from api.models.user import Roles


class AdminStatsView(APIView):
    
    def get(self, request):
        if request.user.role != Roles.ADMIN:
            return Response({"detail": "Forbidden"}, status=403)
        
        objects_in_work = ConstructionObject.objects.filter(
            ~Q(status=ObjectStatus.COMPLETED),
            ssk__isnull=False
        ).count()
        
        open_violations = Prescription.objects.filter(
            status="open"
        ).count()
        
        total_deliveries = Delivery.objects.count()
        
        return Response({
            "objects_in_work": objects_in_work,
            "open_violations": open_violations,
            "total_deliveries": total_deliveries
        }, status=200)
