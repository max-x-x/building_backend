from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response

from api.api.v1.views.utils import RoleRequired
from api.models.user import Roles, User
from api.serializers.users import UsersListOutSerializer, UserOutSerializer  # уже есть

class ForemenListView(APIView):
    """
    GET /api/v1/foremen
    Назначение: получить список всех прорабов.
    Кто: admin, ssk, iko (прорабам обычно не нужно, но можно оставить при желании).
    Фильтры: ?query=...&limit=20&offset=0
    """
    permission_classes = [RoleRequired.as_permitted(Roles.ADMIN, Roles.SSK, Roles.IKO)]

    def get(self, request):
        query = request.query_params.get("query")
        try:
            limit = max(1, min(int(request.query_params.get("limit", 20)), 200))
        except ValueError:
            limit = 20
        try:
            offset = max(0, int(request.query_params.get("offset", 0)))
        except ValueError:
            offset = 0

        qs = User.objects.filter(role=Roles.FOREMAN, is_active=True).order_by("-date_joined")
        if query:
            qs = qs.filter(Q(email__icontains=query) | Q(full_name__icontains=query) | Q(phone__icontains=query))

        total = qs.count()
        users = list(qs[offset: offset + limit])
        out = UsersListOutSerializer({"items": users, "total": total}, context={"request": request})
        return Response(out.data, status=200)
