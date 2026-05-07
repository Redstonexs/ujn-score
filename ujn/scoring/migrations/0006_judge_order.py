from django.db import migrations, models


def populate_judge_order(apps, schema_editor):
    Judge = apps.get_model('scoring', 'Judge')
    for index, judge in enumerate(Judge.objects.order_by('id'), start=1):
        judge.order = index
        judge.save(update_fields=['order'])


class Migration(migrations.Migration):

    dependencies = [
        ('scoring', '0005_add_college_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='judge',
            name='order',
            field=models.IntegerField(default=1, verbose_name='序号'),
        ),
        migrations.RunPython(populate_judge_order, migrations.RunPython.noop),
    ]
