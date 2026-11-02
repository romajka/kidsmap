from django.core.management.base import BaseCommand
from django.db import transaction
from catalog.homepage_copy import HOME_COPY_DEFAULTS, LEGACY_HOME_COPY
from catalog.models import SiteSettings


class Command(BaseCommand):
    help = 'Update known legacy homepage copy, preserving custom editorial text.'

    @transaction.atomic
    def handle(self, *args, **options):
        site = SiteSettings.objects.select_for_update().order_by('id').first()
        changed = []
        if site is not None:
            for field, replacement in HOME_COPY_DEFAULTS.items():
                current = getattr(site, field, '')
                if not current.strip() or current in LEGACY_HOME_COPY[field]:
                    setattr(site, field, replacement)
                    changed.append(field)
            if changed:
                site.save(update_fields=[*changed, 'updated_at'])
        self.stdout.write(f'Homepage copy fields updated: {len(changed)}')
