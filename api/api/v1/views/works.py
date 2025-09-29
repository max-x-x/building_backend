from rest_framework.views import APIView
from rest_framework.response import Response
from api.models.work import Work
from api.models.object import ConstructionObject
from api.models.user import Roles
from api.api.v1.views.objects import _visible_object_ids_for_user, _paginated
from api.serializers.works import WorkOutSerializer, WorkCreateSerializer


class WorksListView(APIView):
    def get(self, request):
        object_id = request.query_params.get("object_id")
        visible = _visible_object_ids_for_user(request.user)
        qs = Work.objects.filter(object_id__in=visible).order_by("-created_at")
        if object_id:
            qs = qs.filter(object_id=object_id)
        page, total = _paginated(qs, request)
        return Response({"items": WorkOutSerializer(page, many=True).data, "total": total}, status=200)

class WorkCreateView(APIView):
    def post(self, request):
        if request.user.role not in (Roles.SSK, Roles.ADMIN):
            return Response({"detail":"Forbidden"}, status=403)
        ser = WorkCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            obj = ConstructionObject.objects.get(id=ser.validated_data["object_id"])
        except ConstructionObject.DoesNotExist:
            return Response({"detail":"Object not found"}, status=404)
        if request.user.role != Roles.ADMIN and obj.ssk_id != request.user.id:
            return Response({"detail":"Forbidden"}, status=403)
        w = Work.objects.create(
            object=obj,
            title=ser.validated_data["title"],
            status=ser.validated_data["status"],
            responsible_id=ser.validated_data["responsible_id"],
            reviewer_id=ser.validated_data["reviewer_id"],
        )
        return Response(WorkOutSerializer(w).data, status=201)
