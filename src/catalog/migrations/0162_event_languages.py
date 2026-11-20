# Languages an event is held in ("az,ru"); shown on cards and used by the afisha filter.
#
# NOTE for merging: on this branch the previous migration is 0158. On main, other work
# adds 0159_official_review_responses, 0160_preserve_hidden_replies_on_rollback and
# 0161_event_slug_only_urls; once they are committed, point the dependency below at
# ('catalog', '0161_event_slug_only_urls') so the graph stays linear.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0158_specialist_proposal_qualifications'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='languages',
            field=models.CharField(blank=True, db_default='', default='', max_length=32, verbose_name='Языки проведения'),
        ),
    ]
