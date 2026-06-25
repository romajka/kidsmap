from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext_lazy as _

def render_primary_action(url: str, label: str) -> str:
    """Renders the primary 'Edit' button with SVG icon for admin row actions."""
    return format_html(
        '<a class="km-admin-action km-admin-action--primary" href="{}"><svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" style="margin-right: 4px;"><path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>{}</a>',
        url,
        label,
    )

def render_action_menu(actions: list[tuple[str | None, str, str]]) -> str:
    """
    Renders the three-dot dropdown menu for row actions.
    actions should be a list of tuples: (url, label, style_class)
    If url is None, it renders a span (useful for hints/text).
    """
    if not actions:
        return ""
        
    menu_links = []
    for url, label, style_class in actions:
        if url is None:
            menu_links.append(format_html('<span class="{}">{}</span>', style_class or "km-admin-action-menu__hint", label))
        elif style_class:
            menu_links.append(format_html('<a class="km-admin-action-menu__link {}" href="{}">{}</a>', style_class, url, label))
        else:
            menu_links.append(format_html('<a class="km-admin-action-menu__link" href="{}">{}</a>', url, label))
            
    menu_content = format_html_join("", "{}", ((link,) for link in menu_links))
    return format_html(
        '<details class="km-admin-action-menu"><summary class="km-admin-action-menu__toggle" aria-label="{}">⋮</summary><div class="km-admin-action-menu__panel">{}</div></details>',
        _("Действия"),
        menu_content,
    )

def render_row_actions_container(primary_action: str, menu_html: str) -> str:
    """Wraps primary action and menu in the row container."""
    return format_html(
        '<div class="km-place-row-actions">{} {}</div>',
        primary_action,
        menu_html,
    )

def build_admin_query_string(request, clear: tuple[str, ...] = (), **updates) -> str:
    """Builds a query string for filtering admin lists while maintaining other params."""
    params = request.GET.copy()
    params.pop("p", None)
    for key in clear:
        params.pop(key, None)
    for key, value in updates.items():
        if value in (None, ""):
            params.pop(key, None)
        else:
            params[key] = str(value)
    encoded = params.urlencode()
    return f"?{encoded}" if encoded else ""
