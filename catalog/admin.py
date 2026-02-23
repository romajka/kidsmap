from django.contrib import admin
from .models import Place


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("name_ru", "category", "district", "is_active", "is_verified")
    list_filter = ("category", "district", "is_active", "is_verified")
    search_fields = ("name_ru", "name_en", "address", "instagram", "phone1")
    list_editable = ("is_active", "is_verified")
