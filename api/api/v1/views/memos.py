from rest_framework.views import APIView
from rest_framework.response import Response
from api.models.memo import Memo
from api.api.v1.views.objects import _paginated
from api.api.v1.views.utils import RoleRequired
from api.models.user import Roles
from api.serializers.memos import MemoOutSerializer, MemoCreateSerializer


class MemosView(APIView):
    def get(self, request):
        qs = Memo.objects.all().order_by("-created_at")
        page, total = _paginated(qs, request)
        return Response({"items": MemoOutSerializer(page, many=True).data, "total": total}, status=200)

    permission_classes_post = [RoleRequired.as_permitted(Roles.ADMIN)]
    def post(self, request):
        for perm in self.permission_classes_post:
            if not perm().has_permission(request, self):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied()
        ser = MemoCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        m = Memo.objects.create(**ser.validated_data)
        return Response({"id": m.id, "uuid_memo": str(m.uuid_memo)}, status=201)
