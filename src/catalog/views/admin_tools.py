"""Small staff-only helper views used by the admin."""

from django.shortcuts import render
from django.utils.translation import gettext as _
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def admin_add_choice(request):
    context = admin.site.each_context(request)
    context.update(
        {
            "title": _("Добавить публикацию"),
            "has_permission": True,
        }
    )
    return render(
        request,
        "admin/add_choice.html",
        context,
    )
