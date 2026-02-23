from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Place


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("display_name", "category", "district", "is_active", "is_verified")
    list_filter = ("category", "district", "is_active", "is_verified")
    search_fields = ("name_ru", "name_en", "name", "address", "instagram", "phone1")
    list_editable = ("is_active", "is_verified")

    @admin.display(description=_("Название"))
    def display_name(self, obj):
        return obj.name_ru or obj.name
