from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scoring', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteconfig',
            name='category_field_name',
            field=models.CharField(default='类别', max_length=100, verbose_name='类别字段名'),
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='description_field_name',
            field=models.CharField(default='备注', max_length=100, verbose_name='备注字段名'),
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='exclude_extreme_scores',
            field=models.BooleanField(default=False, help_text='开启后，统计总分与平均分时会在有效评分数大于等于3时去掉一条最高分和一条最低分。', verbose_name='统计时去掉最高分和最低分'),
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='judge_field_name',
            field=models.CharField(default='评委', max_length=100, verbose_name='评委字段名'),
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='judge_sheet_name',
            field=models.CharField(default='评委数据', max_length=100, verbose_name='Excel评委Sheet名称'),
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='order_field_name',
            field=models.CharField(default='序号', max_length=100, verbose_name='序号字段名'),
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='participant_field_name',
            field=models.CharField(default='选手', max_length=100, verbose_name='选手字段名'),
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='participant_sheet_name',
            field=models.CharField(default='选手数据', max_length=100, verbose_name='Excel选手Sheet名称'),
        ),
        migrations.AlterField(
            model_name='siteconfig',
            name='base_url',
            field=models.CharField(default='http://localhost:5173', help_text='用于生成管理员与评委二维码链接，例如 https://score.example.com', max_length=500, verbose_name='前端基础URL'),
        ),
        migrations.AlterField(
            model_name='siteconfig',
            name='site_name',
            field=models.CharField(default='评分系统', max_length=200, verbose_name='活动标题'),
        ),
    ]
