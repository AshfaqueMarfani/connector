"""
Health check views for load balancer / monitoring.
"""

from django.db import connection
from django.http import JsonResponse
from django.views import View
from django.conf import settings


class HealthCheckView(View):
    """
    Unauthenticated health check endpoint.
    Returns 200 with service status for load balancers and monitoring.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        health = {
            "status": "healthy",
            "version": "1.0.0",
            "services": {},
        }

        # Check database connectivity
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health["services"]["database"] = "up"
        except Exception:
            health["services"]["database"] = "down"
            health["status"] = "degraded"

        # Check Redis / Channel layer
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.send)(
                "health-check", {"type": "health.check"}
            )
            async_to_sync(channel_layer.receive)("health-check")
            health["services"]["redis"] = "up"
        except Exception:
            health["services"]["redis"] = "down"
            health["status"] = "degraded"

        # Check Celery broker
        try:
            from celery import current_app

            conn = current_app.connection()
            conn.ensure_connection(max_retries=1, timeout=3)
            conn.close()
            health["services"]["celery_broker"] = "up"
        except Exception:
            health["services"]["celery_broker"] = "down"
            health["status"] = "degraded"

        status_code = 200 if health["status"] == "healthy" else 503
        return JsonResponse(health, status=status_code)


class ReadinessCheckView(View):
    """
    Readiness probe – returns 200 only when all critical services are available.
    Used by Kubernetes / orchestrators to determine if the pod can receive traffic.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return JsonResponse({"ready": True}, status=200)
        except Exception:
            return JsonResponse({"ready": False}, status=503)
