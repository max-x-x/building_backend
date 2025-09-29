from rest_framework.views import APIView
from rest_framework.response import Response
from api.models.ticket import Ticket
from api.models.object import ConstructionObject
from api.models.user import Roles
from api.api.v1.views.objects import _paginated
from api.serializers.tickets import TicketOutSerializer, TicketCreateSerializer


class TicketsView(APIView):
    def get(self, request):
        status_q = request.query_params.get("status")
        qs = Ticket.objects.all().order_by("-created_at")
        if request.user.role != Roles.ADMIN:
            qs = qs.filter(author=request.user)
        if status_q:
            qs = qs.filter(status=status_q)
        page, total = _paginated(qs, request)
        return Response({"items": TicketOutSerializer(page, many=True).data, "total": total}, status=200)

    def post(self, request):
        ser = TicketCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        obj = None
        if "object_id" in ser.validated_data:
            try:
                obj = ConstructionObject.objects.get(id=ser.validated_data["object_id"])
            except ConstructionObject.DoesNotExist:
                return Response({"detail":"Object not found"}, status=404)
        t = Ticket.objects.create(author=request.user, object=obj, text=ser.validated_data["text"])
        return Response(TicketOutSerializer(t).data, status=201)

class TicketSetStatusView(APIView):
    def post(self, request, id: str):
        if request.user.role != Roles.ADMIN:
            return Response({"detail":"Forbidden"}, status=403)
        new_status = request.data.get("status")
        if new_status not in ("open","in_progress","done"):
            return Response({"detail":"bad status"}, status=400)
        try:
            t = Ticket.objects.get(uuid_ticket=id)  # принимаем UUID из пути
        except Ticket.DoesNotExist:
            return Response({"detail":"Not found"}, status=404)
        t.status = new_status
        t.save(update_fields=["status","modified_at"])
        return Response(TicketOutSerializer(t).data, status=200)
