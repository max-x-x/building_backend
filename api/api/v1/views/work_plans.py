from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.serializers.work_plans import WorkPlanCreateSerializer, WorkPlanOutSerializer

class WorkPlanCreateView(APIView):
    """
    POST /api/v1/work-plans
    Назначение: ССК объекта прикрепляет перечень работ.
    Побочный эффект: автоматически создаётся расписание из позиций.
    Тело:
    {
      "object_id": "...",
      "title": "ЭС по договору №...",
      "items": [
        {"name": "Подготовка", "quantity": 1, "unit": "этап", "start_date": "2025-10-01", "end_date": "2025-10-03"},
        {"name": "Земляные работы", "quantity": 150, "unit": "м3", "start_date": "2025-10-04", "end_date": "2025-10-10"}
      ]
    }
    """
    def post(self, request):
        ser = WorkPlanCreateSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        plan = ser.save()
        return Response(WorkPlanOutSerializer(plan).data, status=status.HTTP_201_CREATED)
