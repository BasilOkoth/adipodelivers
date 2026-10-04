from django.db import migrations, models
import impact.models


class Migration(migrations.Migration):
    dependencies = [('impact', '0005_tenant_media_paths')]

    operations = [
        migrations.AddField(model_name='tenant', name='leader_photo', field=models.ImageField(blank=True, upload_to=impact.models.tenant_branding_upload_to)),
        migrations.AddField(model_name='tenant', name='tv_intro_kicker', field=models.CharField(blank=True, default='PUBLIC IMPACT CHANNEL', max_length=120)),
        migrations.AddField(model_name='tenant', name='tv_intro_headline', field=models.CharField(blank=True, default='Impact you can see.', max_length=180)),
        migrations.AddField(model_name='tenant', name='tv_intro_subheadline', field=models.CharField(blank=True, default='Projects, places and evidence from across the constituency.', max_length=300)),
        migrations.AddField(model_name='tenant', name='tv_ticker_text', field=models.CharField(blank=True, default='Projects • Exact locations • Photos • Videos • Evidence • Ward-by-ward impact', max_length=500)),
        migrations.AddField(model_name='tenant', name='tv_show_leader_photo', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='tenant', name='tv_show_qr', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='tenant', name='tv_show_clock', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='tenant', name='tv_show_ticker', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='tenant', name='tv_show_website', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='tenant', name='tv_show_project_status', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='tenant', name='tv_intro_duration_seconds', field=models.PositiveIntegerField(default=8)),
        migrations.AlterField(model_name='tenant', name='logo', field=models.ImageField(blank=True, upload_to=impact.models.tenant_branding_upload_to)),
        migrations.AlterField(model_name='tenant', name='qr_image', field=models.ImageField(blank=True, upload_to=impact.models.tenant_branding_upload_to)),
    ]
