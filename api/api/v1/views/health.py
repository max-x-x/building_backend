import uuid
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

STARTED_AT = timezone.now()

class PingView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        result = {
            "status": "ok",
            "time": timezone.now().isoformat(),
            "started_at": STARTED_AT.isoformat(),
            "debug": bool(settings.DEBUG),
            "version": getattr(settings, "RELEASE", None) or getattr(settings, "VERSION", None),
            "components": {},
        }

        db_ok, db_err = True, None
        try:
            with connection.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        except Exception as e:
            db_ok, db_err = False, str(e)
        result["components"]["database"] = {"ok": db_ok, "error": db_err}

        cache_ok, cache_err = True, None
        try:
            key = f"health:{uuid.uuid4()}"
            cache.set(key, "1", 5)
            cache_ok = cache.get(key) == "1"
        except Exception as e:
            cache_ok, cache_err = False, str(e)
        result["components"]["cache"] = {"ok": cache_ok, "error": cache_err}

        pending = None
        try:
            from django.db.migrations.executor import MigrationExecutor
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            pending = len(plan)
        except Exception:
            pending = None
        result["components"]["migrations"] = {"pending": pending}

        if not db_ok:
            result["status"] = "error"
            return Response(result, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if not cache_ok:
            result["status"] = "degraded"
            return Response(result, status=status.HTTP_200_OK)

        return Response(result, status=status.HTTP_200_OK)
