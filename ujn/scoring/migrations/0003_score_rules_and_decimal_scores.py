from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scoring', '0002_admin_config_and_import_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteconfig',
            name='allow_duplicate_scores',
            field=models.BooleanField(default=True, verbose_name='允许重复打分'),
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='score_value_type',
            field=models.CharField(choices=[('integer', '整数'), ('decimal', '小数')], default='integer', max_length=20, verbose_name='合法打分类型'),
        ),
        migrations.AlterField(
            model_name='score',
            name='score',
            field=models.DecimalField(decimal_places=2, max_digits=8, verbose_name='分数'),
        ),
        migrations.AlterField(
            model_name='siteconfig',
            name='score_max',
            field=models.DecimalField(decimal_places=2, default=Decimal('100.00'), max_digits=8, verbose_name='最高分'),
        ),
        migrations.AlterField(
            model_name='siteconfig',
            name='score_min',
            field=models.DecimalField(decimal_places=2, default=Decimal('1.00'), max_digits=8, verbose_name='最低分'),
        ),
    ]
