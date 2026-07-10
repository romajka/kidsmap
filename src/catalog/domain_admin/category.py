import os

from django.conf import settings
from django.contrib import admin
from django.core.files.storage import FileSystemStorage
from django.db.models import Count, Prefetch, Q
from django import forms
from django.http import JsonResponse
from django.urls import path
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

from catalog.models import Category, Subcategory


class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 1
    fields = ("name_ru", "name_az", "name_en", "order")


def save_uploaded_category_icon(uploaded_file, category_code="category-icon"):
    ext = (uploaded_file.name.rsplit(".", 1)[-1] if "." in uploaded_file.name else "").lower()
    if f".{ext}" not in [".svg", ".png", ".jpg", ".jpeg", ".webp"]:
        raise forms.ValidationError(_("Поддерживаются только SVG, PNG, JPG, JPEG и WEBP."))

    storage = FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)
    safe_code = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in (category_code or "category-icon")).strip("-")
    safe_code = safe_code or "category-icon"
    filename = storage.get_available_name(f"cat_icons/{safe_code}.{ext}")
    saved_name = storage.save(filename, uploaded_file)
    return storage.url(saved_name)


class CategoryAdminForm(forms.ModelForm):
    name = forms.CharField(widget=forms.HiddenInput(), required=False)
    name_az = forms.CharField(label=_("Название (AZ)"), required=True)
    icon_upload = forms.FileField(
        label=_("Файл иконки"),
        required=False,
        help_text=_("Загрузите SVG, PNG, JPG, JPEG или WEBP. Это поле сохраняет файл отдельно, а текстовое поле ниже остаётся запасным вариантом для пути или CSS-класса."),
    )

    class Meta:
        model = Category
        fields = "__all__"
        widgets = {
            "code": forms.TextInput(attrs={"autocomplete": "off", "placeholder": _("Например: education")}),
            "order": forms.NumberInput(attrs={"min": 0, "step": 1, "inputmode": "numeric"}),
            "name_ru": forms.TextInput(attrs={"placeholder": _("Например: Образование")}),
            "name_en": forms.TextInput(attrs={"placeholder": _("Например: Education")}),
            "icon": forms.TextInput(attrs={"autocomplete": "off", "placeholder": _("Например: icons/categories/sports.svg")}),
            "color_bg": forms.TextInput(attrs={"type": "color"}),
            "color_text": forms.TextInput(attrs={"type": "color"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        name_az = cleaned_data.get("name_az")
        if name_az:
            cleaned_data["name"] = name_az
        return cleaned_data

    def clean_icon_upload(self):
        uploaded_file = self.cleaned_data.get("icon_upload")
        if not uploaded_file:
            return uploaded_file
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in [".svg", ".png", ".jpg", ".jpeg", ".webp"]:
            raise forms.ValidationError(_("Поддерживаются только SVG, PNG, JPG, JPEG и WEBP."))
        return uploaded_file

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name_az"].widget.attrs.setdefault("placeholder", _("Например: Təhsil"))
        self.fields["icon"].label = _("Путь или CSS-класс")
        self.fields["icon"].help_text = _(
            "Можно указать относительный путь к иконке или CSS-класс. Например: icons/categories/sports.svg или fas fa-futbol."
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        uploaded_file = self.cleaned_data.get("icon_upload")
        if uploaded_file:
            instance.icon = save_uploaded_category_icon(uploaded_file, self.cleaned_data.get("code") or instance.code)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    change_form_template = "admin/catalog/category/change_form.html"
    list_display = ("code", "name_ru", "name_az", "name_en")
    search_fields = ("code", "name_ru", "name_az", "name_en")
    ordering = ("name_ru",)
    inlines = [SubcategoryInline]

    fieldsets = (
        (None, {
            "fields": (
                ("code", "name_az"),
                ("name_ru", "name_en"),
                "icon",
                ("color_bg", "color_text"),
                "name",
            )
        }),
    )

    def get_inlines(self, request, obj=None):
        if not obj or request.GET.get("_popup"):
            return []
        return self.inlines

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('upload-icon/', self.admin_site.admin_view(self.upload_icon_view), name='catalog_category_upload_icon'),
            path('toggle-active/', self.admin_site.admin_view(self.toggle_active_view), name='catalog_taxonomy_toggle_active'),
        ]
        return custom_urls + urls

    def toggle_active_view(self, request):
        from django.http import JsonResponse
        from catalog.models.category import Category, Subcategory
        
        if request.method != "POST":
            return JsonResponse({"error": "POST required"}, status=405)
            
        if not self.has_change_permission(request):
            return JsonResponse({"error": "Permission denied"}, status=403)
            
        obj_type = request.POST.get('obj_type')
        obj_id = request.POST.get('obj_id')
        
        if obj_type == 'category':
            obj = Category.objects.filter(pk=obj_id).first()
        elif obj_type == 'subcategory':
            obj = Subcategory.objects.filter(pk=obj_id).first()
        else:
            return JsonResponse({"error": "Invalid obj_type"}, status=400)
            
        if not obj:
            return JsonResponse({"error": "Object not found"}, status=404)
            
        obj.is_active = not obj.is_active
        obj.save(update_fields=['is_active'])
        
        return JsonResponse({"status": "success", "is_active": obj.is_active})

    def changelist_view(self, request, extra_context=None):
        from django.db.models import Prefetch, Count, Q
        from catalog.models.category import Category, Subcategory
        from django.template.response import TemplateResponse
        from django.utils.translation import gettext as _

        search_query = request.GET.get('q', '').strip()
        
        categories = Category.objects.all()
        subcategories = Subcategory.objects.all()

        if search_query:
            sub_matches = subcategories.filter(
                Q(code__icontains=search_query) |
                Q(name_ru__icontains=search_query) |
                Q(name_az__icontains=search_query) |
                Q(name_en__icontains=search_query)
            )
            cat_ids_from_subs = sub_matches.values_list('category_id', flat=True)
            
            categories = categories.filter(
                Q(code__icontains=search_query) |
                Q(name_ru__icontains=search_query) |
                Q(name_az__icontains=search_query) |
                Q(name_en__icontains=search_query) |
                Q(code__in=cat_ids_from_subs)
            )

        # Annotate counts and optimize queries
        categories = categories.annotate(
            places_count=Count('place', distinct=True),
            sub_count=Count('subcategories', distinct=True)
        ).order_by('name_ru')

        sub_qs = Subcategory.objects.annotate(
            places_count=Count('place')
        ).order_by('name_ru')

        categories = categories.prefetch_related(
            Prefetch('subcategories', queryset=sub_qs)
        )

        context = {
            **self.admin_site.each_context(request),
            'title': _('Категории и подкатегории'),
            'categories': categories,
            'search_query': search_query,
            'opts': self.model._meta,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request),
            'app_label': self.model._meta.app_label,
        }
        context.update(extra_context or {})
        return TemplateResponse(request, "admin/catalog/category/change_list.html", context)

    def upload_icon_view(self, request):
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        try:
            media_url = save_uploaded_category_icon(uploaded_file, request.POST.get("code") or "category-icon")
        except forms.ValidationError as exc:
            return JsonResponse({"error": exc.messages[0]}, status=400)
        except Exception as exc:
            return JsonResponse({"error": f"Failed to save file: {str(exc)}"}, status=500)

        return JsonResponse({"success": True, "url": media_url, "path": media_url})



@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ("name_ru", "category", "name_az", "name_en")
    list_filter = ("category",)
    search_fields = ("name_ru", "name_az", "name_en")
    ordering = ("category", "name_ru")
    exclude = ("code", "order")

    def has_module_permission(self, request):
        # Скрываем подкатегории из бокового меню, так как они управляются из Категорий
        return False
