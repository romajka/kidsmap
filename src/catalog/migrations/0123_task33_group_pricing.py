from django.db import migrations, models
from django.db.models import Q
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("catalog", "0122_task33_server_draft")]
    operations = [
        migrations.AlterField(model_name="pricingplan", name="place", field=models.ForeignKey(to="catalog.place", null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, related_name="pricing_plan_records")),
        migrations.AddField(model_name="pricingplan", name="offering_group", field=models.ForeignKey(to="catalog.offeringgroup", null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, related_name="pricing_plan_records")),
        migrations.AddField(model_name="pricingplan", name="is_trial", field=models.BooleanField(default=False)),
        migrations.AddConstraint(model_name="pricingplan", constraint=models.CheckConstraint(condition=(Q(place__isnull=False, offering_group__isnull=True) | Q(place__isnull=True, offering_group__isnull=False)), name="pricing_exactly_one_target")),
        migrations.AddIndex(model_name="pricingplan", index=models.Index(fields=("offering_group", "is_active", "charge_role", "currency"), name="pricing_group_lookup_idx")),
    ]
