from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.api.v1.views.objects import _visible_object_ids_for_user, _paginated
from api.serializers.documents import DocumentOutSerializer, ExecDocCreateSerializer, ExecDocOutSerializer
from api.models.documents import DocumentFile, ExecDocument
from api.models.object import ConstructionObject
from api.models.user import Roles
from api.api.v1.views.utils import RoleRequired

class DocumentsListView(APIView):
    def get(self, request):
        object_id = request.query_params.get("object_id")
        if not object_id:
            return Response({"detail":"object_id is required"}, status=400)
        visible = _visible_object_ids_for_user(request.user)
        qs = DocumentFile.objects.filter(object_id=object_id, object_id__in=visible).order_by("-created_at")
        page, total = _paginated(qs, request)
        return Response({"items": DocumentOutSerializer(page, many=True).data, "total": total}, status=200)

class ExecDocsView(APIView):
    permission_classes_post = [RoleRequired.as_permitted(Roles.SSK, Roles.IKO, Roles.ADMIN)]

    def get(self, request):
        object_id = request.query_params.get("object_id")
        if not object_id:
            return Response({"detail":"object_id is required"}, status=400)
        visible = _visible_object_ids_for_user(request.user)
        qs = ExecDocument.objects.filter(object_id=object_id, object_id__in=visible).order_by("-created_at")
        page, total = _paginated(qs, request)
        return Response({"items": ExecDocOutSerializer(page, many=True).data, "total": total}, status=200)

    def post(self, request):
        for perm in self.permission_classes_post:
            if not perm().has_permission(request, self):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied()
        ser = ExecDocCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            obj = ConstructionObject.objects.get(id=ser.validated_data["object_id"])
        except ConstructionObject.DoesNotExist:
            return Response({"detail":"Object not found"}, status=404)
        ed = ExecDocument.objects.create(
            object=obj,
            kind=ser.validated_data["kind"],
            pdf_url=ser.validated_data["pdf_url"],
            created_by=request.user
        )
        return Response(ExecDocOutSerializer(ed).data, status=201)
