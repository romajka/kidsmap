from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0071_category_subcategory_audit_softdelete")]

    operations = [
        migrations.AddField(
            model_name="subcategory",
            name="icon",
            field=models.CharField(blank=True, default="", help_text="Путь к загруженной иконке", max_length=255, verbose_name="Иконка"),
        ),
    ]
