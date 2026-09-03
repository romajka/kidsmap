from django.db import migrations


LEGACY_EMAIL = "kidsmap.az@gmail.com"
OFFICIAL_EMAIL = "info@kidsmap.az"


def replace_legacy_gmail_contact(apps, schema_editor):
    SiteSettings = apps.get_model("catalog", "SiteSettings")
    obj = SiteSettings.objects.order_by("id").first()
    if not obj:
        return

    changed_fields = []
    if (obj.footer_email or "").strip().lower() == LEGACY_EMAIL:
        obj.footer_email = OFFICIAL_EMAIL
        changed_fields.append("footer_email")

    for field_name in ("contacts_text_ru", "contacts_text_en", "contacts_text_az"):
        value = getattr(obj, field_name) or ""
        if LEGACY_EMAIL in value.lower():
            setattr(obj, field_name, value.replace(LEGACY_EMAIL, OFFICIAL_EMAIL))
            changed_fields.append(field_name)

    if changed_fields:
        obj.save(update_fields=[*sorted(set(changed_fields)), "updated_at"])


class Migration(migrations.Migration):
    dependencies = [("catalog", "0097_drop_legacy_userprofile_roles")]

    operations = [
        migrations.RunPython(replace_legacy_gmail_contact, migrations.RunPython.noop),
    ]
