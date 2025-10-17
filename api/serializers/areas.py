from rest_framework import serializers
from api.models.area import Area, SubArea
from api.models.work_plan import WorkItem


class AreaCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Area
        fields = ("name", "geometry", "object")
    
    def validate_geometry(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Geometry должен быть объектом")
        
        geom_type = value.get("type")
        if geom_type not in ["Polygon", "MultiPolygon"]:
            raise serializers.ValidationError("Поддерживаются только Polygon и MultiPolygon")
        
        coordinates = value.get("coordinates")
        if not coordinates or not isinstance(coordinates, list):
            raise serializers.ValidationError("Отсутствуют или некорректны coordinates")
        
        if geom_type == "Polygon":
            if not isinstance(coordinates, list) or len(coordinates) == 0:
                raise serializers.ValidationError("Polygon должен содержать массив колец")
            for ring in coordinates:
                if not isinstance(ring, list) or len(ring) < 4:
                    raise serializers.ValidationError("Каждое кольцо должно содержать минимум 4 точки")
                for point in ring:
                    if not isinstance(point, list) or len(point) != 2:
                        raise serializers.ValidationError("Каждая точка должна содержать [lon, lat]")
        
        elif geom_type == "MultiPolygon":
            if not isinstance(coordinates, list) or len(coordinates) == 0:
                raise serializers.ValidationError("MultiPolygon должен содержать массив полигонов")
            for polygon in coordinates:
                if not isinstance(polygon, list) or len(polygon) == 0:
                    raise serializers.ValidationError("Каждый полигон должен содержать массив колец")
        
        return value


class AreaOutSerializer(serializers.ModelSerializer):
    geometry_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Area
        fields = ("id", "uuid_area", "name", "geometry", "geometry_type", "object", "created_at", "modified_at")
    
    def get_geometry_type(self, obj):
        return obj.get_geometry_type()


class AreaListOutSerializer(serializers.Serializer):
    items = AreaOutSerializer(many=True)
    total = serializers.IntegerField()


class SubAreaCreateSerializer(serializers.ModelSerializer):
    area_id = serializers.IntegerField(write_only=True)
    work_item_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = SubArea
        fields = ("name", "geometry", "color", "area_id", "work_item_id")

    def validate_geometry(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Geometry должен быть объектом")
        geom_type = value.get("type")
        if geom_type not in ["Polygon", "MultiPolygon"]:
            raise serializers.ValidationError("Поддерживаются только Polygon и MultiPolygon")
        coordinates = value.get("coordinates")
        if not coordinates or not isinstance(coordinates, list):
            raise serializers.ValidationError("Отсутствуют или некорректны coordinates")
        return value

    def validate(self, data):
        try:
            area = Area.objects.get(id=data["area_id"])
        except Area.DoesNotExist:
            raise serializers.ValidationError({"area_id": "Область не найдена"})
        data["area"] = area

        work_item_id = data.get("work_item_id")
        if work_item_id is not None:
            try:
                data["work_item"] = WorkItem.objects.get(id=work_item_id)
            except WorkItem.DoesNotExist:
                raise serializers.ValidationError({"work_item_id": "WorkItem не найден"})
        else:
            data["work_item"] = None
        return data

    def create(self, validated_data):
        validated_data.pop("area_id", None)
        validated_data.pop("work_item_id", None)
        return SubArea.objects.create(**validated_data)


class SubAreaOutSerializer(serializers.ModelSerializer):
    geometry_type = serializers.SerializerMethodField()

    class Meta:
        model = SubArea
        fields = ("id", "name", "geometry", "geometry_type", "color", "area", "work_item", "created_at", "modified_at")

    def get_geometry_type(self, obj):
        return obj.get_geometry_type()
