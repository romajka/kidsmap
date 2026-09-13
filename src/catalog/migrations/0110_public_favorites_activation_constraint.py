from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0109_alter_analytics_choices_and_threshold")]

    operations = [
        migrations.AddConstraint(
            model_name="sitesettings",
            constraint=models.CheckConstraint(
                condition=models.Q(("public_favorites_count_enabled", False), ("public_favorites_minimum__isnull", False), _connector="OR"),
                name="public_favorites_requires_threshold",
            ),
        )
    ]
