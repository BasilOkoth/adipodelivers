from django.db import migrations, models


def mark_known_seeded_records(apps, schema_editor):
    Project = apps.get_model('impact', 'Project')
    Project.objects.filter(record_id__in=['WEST-ROAD-001', 'WANG-EDU-001']).update(entry_source='seeded')


class Migration(migrations.Migration):
    dependencies = [('impact', '0006_premium_tv_experience')]

    operations = [
        migrations.AddField(
            model_name='project',
            name='entry_source',
            field=models.CharField(
                choices=[('manual','Manual entry'),('imported','Imported from update'),('seeded','Seeded / starter record')],
                default='manual', max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='project',
            name='story_priority',
            field=models.CharField(
                choices=[('standard','Standard'),('featured','Featured'),('flagship','Flagship')],
                default='standard', max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='projectmedia',
            name='is_cover',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='projectmedia',
            name='uploaded_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.RunPython(mark_known_seeded_records, migrations.RunPython.noop),
    ]
