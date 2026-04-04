import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scoring', '0004_alter_siteconfig_score_value_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='college',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='学院'),
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='college_field_name',
            field=models.CharField(default='学院', max_length=100, verbose_name='学院字段名'),
        ),
    ]
