"""
Django admin configuration for the locations app.
"""

from django.contrib.gis import admin as gis_admin

from .models import LocationHistory, UserLocation


@gis_admin.register(UserLocation)
class UserLocationAdmin(gis_admin.GISModelAdmin):
    list_display = [
        "user",
        "get_lat",
        "get_lon",
        "source",
        "accuracy_meters",
        "is_background_tracking",
        "updated_at",
    ]
    list_filter = ["source", "is_background_tracking"]
    search_fields = ["user__email", "user__full_name"]
    readonly_fields = ["id", "updated_at", "created_at"]
    raw_id_fields = ["user"]

    @gis_admin.display(description="Latitude")
    def get_lat(self, obj):
        return round(obj.point.y, 6) if obj.point else None

    @gis_admin.display(description="Longitude")
    def get_lon(self, obj):
        return round(obj.point.x, 6) if obj.point else None


@gis_admin.register(LocationHistory)
class LocationHistoryAdmin(gis_admin.GISModelAdmin):
    list_display = ["user", "source", "recorded_at"]
    list_filter = ["source"]
    search_fields = ["user__email"]
    readonly_fields = ["id", "recorded_at"]
    raw_id_fields = ["user"]
    date_hierarchy = "recorded_at"
