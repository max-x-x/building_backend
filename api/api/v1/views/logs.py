from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from api.models import Roles
from api.models.log import Log, LogLevel, LogCategory
from api.api.v1.views.objects import _paginated


class LogsListView(APIView):
    
    def get(self, request):
        if request.user.role != Roles.ADMIN:
            return Response({"detail": "Forbidden"}, status=403)
        
        qs = Log.objects.select_related("user").all()
        
        level = request.query_params.get("level")
        if level and level in [choice[0] for choice in LogLevel.choices]:
            qs = qs.filter(level=level)
        
        category = request.query_params.get("category")
        if category and category in [choice[0] for choice in LogCategory.choices]:
            qs = qs.filter(category=category)
        
        user_id = request.query_params.get("user_id")
        if user_id:
            qs = qs.filter(user_id=user_id)
        
        object_id = request.query_params.get("object_id")
        if object_id:
            qs = qs.filter(object_id=object_id)
        
        date_from = request.query_params.get("date_from")
        if date_from:
            try:
                date_from = timezone.datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                qs = qs.filter(created_at__gte=date_from)
            except ValueError:
                pass
        
        date_to = request.query_params.get("date_to")
        if date_to:
            try:
                date_to = timezone.datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                qs = qs.filter(created_at__lte=date_to)
            except ValueError:
                pass
        
        search = request.query_params.get("search")
        if search:
            qs = qs.filter(message__icontains=search)
        
        method = request.query_params.get("method")
        if method:
            qs = qs.filter(request_method=method)
        
        status_code = request.query_params.get("status_code")
        if status_code:
            try:
                status_code = int(status_code)
                qs = qs.filter(response_status=status_code)
            except ValueError:
                pass
        
        page, total = _paginated(qs.order_by("-created_at"), request)
        
        logs_data = []
        for log in page:
            logs_data.append({
                "id": log.id,
                "level": log.level,
                "category": log.category,
                "message": log.message,
                "created_at": log.created_at,
                "modified_at": log.modified_at,
            })
        
        return Response({
            "items": logs_data,
            "total": total
        }, status=200)


class LogsStatsView(APIView):
    
    def get(self, request):
        if request.user.role != Roles.ADMIN:
            return Response({"detail": "Forbidden"}, status=403)
        
        days = int(request.query_params.get("days", 7))
        date_from = timezone.now() - timedelta(days=days)
        
        qs = Log.objects.filter(created_at__gte=date_from)
        
        levels_stats = {}
        for level, _ in LogLevel.choices:
            count = qs.filter(level=level).count()
            levels_stats[level] = count
        
        categories_stats = {}
        for category, _ in LogCategory.choices:
            count = qs.filter(category=category).count()
            categories_stats[category] = count
        
        daily_stats = []
        for i in range(days):
            date = date_from + timedelta(days=i)
            next_date = date + timedelta(days=1)
            count = qs.filter(created_at__gte=date, created_at__lt=next_date).count()
            daily_stats.append({
                "date": date.date().isoformat(),
                "count": count
            })
        
        errors_stats = qs.filter(level__in=['error', 'critical']).count()
        
        return Response({
            "period_days": days,
            "total_logs": qs.count(),
            "levels_stats": levels_stats,
            "categories_stats": categories_stats,
            "daily_stats": daily_stats,
            "errors_count": errors_stats
        }, status=200)
