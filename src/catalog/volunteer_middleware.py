from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

from catalog.services.staff_roles import is_volunteer


class VolunteerAccessMiddleware(MiddlewareMixin):
    """Fail closed on all ordinary admin/owner URLs, including localized aliases.

    The marker restricts even accidentally granted Django permissions. Workspace
    views additionally enforce active staff, ownership and review permissions.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        volunteer = is_volunteer(request.user)
        # AuthenticationMiddleware gives each request its own User instance.
        # Reuse this decision in the sidebar and object-permission services.
        request.user._kidsmap_volunteer_role = volunteer
        if not volunteer:
            return None
        match = request.resolver_match
        name = match.url_name or ""
        if name.startswith("owner_") or name in {"request_place_ownership", "legacy_owner_section", "serve_specialist_document"}:
            raise PermissionDenied
        if match.app_name in {"admin", "localized_admin"} or name == "admin_add_choice":
            if name == "index":
                return redirect("admin:volunteer_index")
            if name not in {
                "volunteer_index", "volunteer_add", "volunteer_edit", "volunteer_detail", "volunteer_photo",
                "login", "logout", "password_change", "password_change_done",
            }:
                raise PermissionDenied
        return None
