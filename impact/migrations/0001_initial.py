from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name='Ward', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('name', models.CharField(max_length=120, unique=True)),
            ('display_order', models.PositiveIntegerField(default=0)),
        ], options={'ordering':['display_order','name']}),
        migrations.CreateModel(name='Project', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('slug', models.SlugField(blank=True, max_length=180, unique=True)),
            ('record_id', models.CharField(max_length=50, unique=True)),
            ('title', models.CharField(max_length=240)),
            ('short_title', models.CharField(blank=True, max_length=160)),
            ('sector', models.CharField(max_length=120)),
            ('intervention', models.CharField(blank=True, max_length=240)),
            ('summary', models.TextField()),
            ('project_location', models.CharField(help_text='Human-readable project location or route', max_length=300)),
            ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
            ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
            ('start_date', models.DateField(blank=True, null=True)), ('completion_date', models.DateField(blank=True, null=True)),
            ('budget', models.DecimalField(blank=True, decimal_places=2, max_digits=16, null=True)),
            ('funding_source', models.CharField(blank=True, max_length=180)), ('implementing_agency', models.CharField(blank=True, max_length=180)),
            ('beneficiaries', models.PositiveIntegerField(blank=True, null=True)),
            ('verification_status', models.CharField(choices=[('submitted','Submitted · verification pending'),('verified','Verified'),('demo','Demo record')], default='submitted', max_length=20)),
            ('source_label', models.CharField(blank=True, max_length=180)), ('source_url', models.URLField(blank=True)),
            ('tv_enabled', models.BooleanField(default=True)), ('published', models.BooleanField(default=True)), ('featured', models.BooleanField(default=False)),
            ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
            ('ward', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='projects', to='impact.ward')),
        ], options={'ordering':['-featured','-updated_at']}),
        migrations.CreateModel(name='ProjectImpact', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('text', models.CharField(max_length=240)), ('display_order', models.PositiveIntegerField(default=0)),
            ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='impacts', to='impact.project')),
        ], options={'ordering':['display_order','id']}),
        migrations.CreateModel(name='ProjectMedia', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('media_type', models.CharField(choices=[('video','Video'),('image','Image')], default='video', max_length=10)),
            ('title', models.CharField(max_length=180)), ('caption', models.CharField(blank=True, max_length=300)),
            ('location_label', models.CharField(blank=True, help_text='Example: Nyapuodi Beach · West Karachuonyo', max_length=180)),
            ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)), ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
            ('local_file', models.FileField(blank=True, upload_to='project-media/')), ('original_s3_key', models.CharField(blank=True, max_length=500)),
            ('hls_manifest_url', models.URLField(blank=True, max_length=1000)), ('mp4_fallback_url', models.URLField(blank=True, max_length=1000)), ('poster_url', models.URLField(blank=True, max_length=1000)),
            ('demo_static_path', models.CharField(blank=True, help_text='Prototype-only static path, e.g. impact/media/road-demo.mp4', max_length=300)),
            ('duration_seconds', models.PositiveIntegerField(default=15)), ('tv_enabled', models.BooleanField(default=True)), ('tv_start_seconds', models.PositiveIntegerField(default=0)), ('tv_end_seconds', models.PositiveIntegerField(blank=True, null=True)), ('show_location_overlay', models.BooleanField(default=True)), ('display_order', models.PositiveIntegerField(default=0)),
            ('evidence_status', models.CharField(choices=[('submitted','Submitted'),('verified','Verified'),('demo','Demonstration')], default='submitted', max_length=20)),
            ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='media', to='impact.project')),
        ], options={'ordering':['display_order','id']}),
        migrations.CreateModel(name='EvidenceDocument', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('title', models.CharField(max_length=180)), ('file', models.FileField(blank=True, upload_to='evidence/')), ('external_url', models.URLField(blank=True)), ('source_organization', models.CharField(blank=True, max_length=180)), ('verified', models.BooleanField(default=False)), ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='impact.project')),
        ]),
    ]
