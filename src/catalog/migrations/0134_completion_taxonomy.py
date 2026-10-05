from django.db import migrations,models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('catalog','0133_task33_event_foundation')]
    operations=[
        migrations.AddField(model_name='program',name='subcategory',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='programs',to='catalog.subcategory')),
        migrations.AddField(model_name='activity',name='category',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='activities',to='catalog.category')),
        migrations.AddField(model_name='activity',name='subcategory',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='activities',to='catalog.subcategory')),
    ]
