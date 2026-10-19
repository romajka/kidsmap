"""Map existing admin menu metadata to the project's rounded SVG symbols."""
from django import template
register=template.Library()
ICONS={
    'folder':'folder','folder-open':'folder','shield-alt':'shield','building':'domain',
    'map-marker-alt':'location_on','book-open':'school','chalkboard-teacher':'history_edu',
    'users':'groups','user-friends':'group','calendar-alt':'event','user-tie':'person',
    'star':'star','trash-alt':'delete','copy':'category','clone':'category',
    'graduation-cap':'school','globe':'public','map-signs':'map','map-marked-alt':'map',
    'subway':'train','user':'person','user-plus':'person_add','user-shield':'admin_panel_settings',
    'images':'photo_library','image':'image','cog':'settings','cogs':'settings',
    'chart-line':'analytics','chart-bar':'assessment','history':'history','search':'search',
    'exclamation-triangle':'warning','tools':'tune','clock':'schedule','key':'key',
    'envelope':'mail','envelope-open-text':'mail','id-badge':'account_circle',
    'th':'apps','fingerprint':'token','link':'link','check':'check_circle',
    'plus':'add','user-circle':'account_circle','th-large':'dashboard',
}

@register.filter
def navigation_icon(value):
    return next((ICONS[token[3:]] for token in str(value or '').split() if token.startswith('fa-') and token[3:] in ICONS),'category')
