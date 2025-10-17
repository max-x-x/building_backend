from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.models.area import Area, SubArea
from api.serializers.areas import AreaCreateSerializer, AreaOutSerializer, AreaListOutSerializer, SubAreaCreateSerializer, SubAreaOutSerializer
from api.api.v1.views.objects import _paginated
from api.utils.logging import log_area_created, log_area_viewed


class AreasCreateView(APIView):
    
    def post(self, request):
        ser = AreaCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        area = ser.save()
        
        object_name = area.object.name if area.object else "Не привязан к объекту"
        log_area_created(area.name, object_name, request.user.full_name, request.user.role)
        
        return Response(AreaOutSerializer(area).data, status=status.HTTP_201_CREATED)


class AreasDetailView(APIView):
    
    def get(self, request, id: int):
        try:
            area = Area.objects.get(id=id)
        except Area.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)
        
        log_area_viewed(area.name, request.user.full_name, request.user.role)
        
        return Response(AreaOutSerializer(area).data, status=200)


class AreasListView(APIView):
    
    def get(self, request):
        qs = Area.objects.all().order_by("-created_at")
        
        name = request.query_params.get("name")
        if name:
            qs = qs.filter(name__icontains=name)
        
        geometry_type = request.query_params.get("geometry_type")
        if geometry_type in ["Polygon", "MultiPolygon"]:
            qs = qs.filter(geometry__type=geometry_type)
        
        page, total = _paginated(qs, request)
        return Response(AreaListOutSerializer({"items": page, "total": total}).data, status=200)


class SubAreasCreateView(APIView):
    def post(self, request):
        ser = SubAreaCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sub = ser.save()
        return Response(SubAreaOutSerializer(sub).data, status=status.HTTP_201_CREATED)
