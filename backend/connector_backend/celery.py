"""
Celery app configuration for connector_backend.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "connector_backend.settings")

app = Celery("connector_backend")

# Read config from Django settings, using the CELERY_ namespace.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """A simple debug/healthcheck task."""
    print(f"Request: {self.request!r}")
