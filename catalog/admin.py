from django.contrib import admin
from .models import Place

@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "district", "metro", "is_verified")
    search_fields = ("name", "district", "metro", "address", "instagram")
    list_filter = ("category", "is_verified", "district")