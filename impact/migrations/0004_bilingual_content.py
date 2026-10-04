from django.db import migrations, models


def configure_adipo_language(apps, schema_editor):
    Tenant = apps.get_model('impact', 'Tenant')
    Tenant.objects.filter(slug='adipodelivers').update(
        primary_language_code='en',
        primary_language_name='English',
        secondary_language_code='luo',
        secondary_language_name='Dholuo',
        secondary_language_short='DHO',
        bilingual_tv_enabled=True,
        default_tv_language_mode='bilingual',
    )


class Migration(migrations.Migration):
    dependencies = [('impact', '0003_multitenant_core')]

    operations = [
        migrations.AddField(model_name='tenant', name='primary_language_code', field=models.CharField(default='en', max_length=12)),
        migrations.AddField(model_name='tenant', name='primary_language_name', field=models.CharField(default='English', max_length=60)),
        migrations.AddField(model_name='tenant', name='secondary_language_code', field=models.CharField(blank=True, max_length=12)),
        migrations.AddField(model_name='tenant', name='secondary_language_name', field=models.CharField(blank=True, max_length=60)),
        migrations.AddField(model_name='tenant', name='secondary_language_short', field=models.CharField(blank=True, max_length=12)),
        migrations.AddField(model_name='tenant', name='bilingual_tv_enabled', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='tenant', name='default_tv_language_mode', field=models.CharField(choices=[('en','English'),('local','Community language'),('bilingual','Bilingual')], default='en', max_length=16)),
        migrations.AddField(model_name='ward', name='name_local', field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name='project', name='title_local', field=models.CharField(blank=True, max_length=240)),
        migrations.AddField(model_name='project', name='short_title_local', field=models.CharField(blank=True, max_length=160)),
        migrations.AddField(model_name='project', name='intervention_local', field=models.CharField(blank=True, max_length=240)),
        migrations.AddField(model_name='project', name='summary_local', field=models.TextField(blank=True)),
        migrations.AddField(model_name='project', name='project_location_local', field=models.CharField(blank=True, max_length=300)),
        migrations.AddField(model_name='projectimpact', name='text_local', field=models.CharField(blank=True, max_length=240)),
        migrations.AddField(model_name='projectmedia', name='caption_local', field=models.CharField(blank=True, max_length=300)),
        migrations.AddField(model_name='projectmedia', name='location_label_local', field=models.CharField(blank=True, max_length=180)),
        migrations.RunPython(configure_adipo_language, migrations.RunPython.noop),
    ]
