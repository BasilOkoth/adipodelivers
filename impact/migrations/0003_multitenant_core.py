from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def seed_default_tenant(apps, schema_editor):
    Tenant = apps.get_model('impact', 'Tenant')
    Ward = apps.get_model('impact', 'Ward')
    Project = apps.get_model('impact', 'Project')
    SourcePost = apps.get_model('impact', 'SourcePost')
    TenantDomain = apps.get_model('impact', 'TenantDomain')

    tenant, _ = Tenant.objects.get_or_create(
        slug='adipodelivers',
        defaults={
            'name': 'AdipoDelivers',
            'public_name': 'Karachuonyo Impact',
            'tagline': 'Public service, made visible.',
            'leader_name': 'Hon. Andrew Adipo Okuome',
            'leader_title': 'Member of Parliament',
            'jurisdiction_name': 'Karachuonyo Constituency',
            'county_name': 'Homa Bay County',
            'country_name': 'Kenya',
            'public_domain': 'adipodelivers.org',
            'brand_mark': 'K',
            'primary_color': '#061421',
            'accent_color': '#e5c176',
            'area_label': '441.2 km²',
            'population_label': '178,686 · 2019',
            'area_unit_singular': 'ward',
            'area_unit_plural': 'wards',
            'is_active': True,
            'is_default': True,
        }
    )
    Ward.objects.filter(tenant__isnull=True).update(tenant=tenant)
    Project.objects.filter(tenant__isnull=True).update(tenant=tenant)
    SourcePost.objects.filter(tenant__isnull=True).update(tenant=tenant)
    TenantDomain.objects.get_or_create(tenant=tenant, domain='adipodelivers.org', defaults={'is_primary': True})
    TenantDomain.objects.get_or_create(tenant=tenant, domain='www.adipodelivers.org', defaults={'is_primary': False})


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('impact', '0002_sourcepost'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=160)),
                ('slug', models.SlugField(max_length=80, unique=True)),
                ('public_name', models.CharField(blank=True, max_length=180)),
                ('tagline', models.CharField(blank=True, max_length=240)),
                ('leader_name', models.CharField(blank=True, max_length=180)),
                ('leader_title', models.CharField(blank=True, max_length=180)),
                ('jurisdiction_name', models.CharField(blank=True, max_length=180)),
                ('county_name', models.CharField(blank=True, max_length=180)),
                ('country_name', models.CharField(default='Kenya', max_length=120)),
                ('public_domain', models.CharField(blank=True, max_length=255)),
                ('brand_mark', models.CharField(default='I', max_length=12)),
                ('primary_color', models.CharField(default='#061421', max_length=20)),
                ('accent_color', models.CharField(default='#e5c176', max_length=20)),
                ('logo', models.ImageField(blank=True, upload_to='tenant-branding/')),
                ('qr_image', models.ImageField(blank=True, upload_to='tenant-branding/')),
                ('area_label', models.CharField(blank=True, max_length=100)),
                ('population_label', models.CharField(blank=True, max_length=100)),
                ('area_unit_singular', models.CharField(default='ward', max_length=60)),
                ('area_unit_plural', models.CharField(default='wards', max_length=60)),
                ('is_active', models.BooleanField(default=True)),
                ('is_default', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='TenantDomain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(max_length=255, unique=True)),
                ('is_primary', models.BooleanField(default=False)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='domains', to='impact.tenant')),
            ],
        ),
        migrations.CreateModel(
            name='TenantMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('owner', 'Owner'), ('admin', 'Administrator'), ('editor', 'Editor'), ('viewer', 'Viewer')], default='editor', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='impact.tenant')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tenant_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={'unique_together': {('tenant', 'user')}},
        ),
        migrations.AddField(
            model_name='ward', name='tenant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='wards', to='impact.tenant'),
        ),
        migrations.AddField(
            model_name='project', name='tenant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='impact.tenant'),
        ),
        migrations.AddField(
            model_name='sourcepost', name='tenant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='source_posts', to='impact.tenant'),
        ),
        migrations.RunPython(seed_default_tenant, migrations.RunPython.noop),
        migrations.AlterField(model_name='ward', name='name', field=models.CharField(max_length=120)),
        migrations.AlterField(model_name='project', name='slug', field=models.SlugField(blank=True, max_length=180)),
        migrations.AlterField(model_name='project', name='record_id', field=models.CharField(max_length=50)),
        migrations.AlterField(model_name='ward', name='tenant', field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wards', to='impact.tenant')),
        migrations.AlterField(model_name='project', name='tenant', field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='impact.tenant')),
        migrations.AlterField(model_name='sourcepost', name='tenant', field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='source_posts', to='impact.tenant')),
        migrations.AlterUniqueTogether(name='ward', unique_together={('tenant', 'name')}),
        migrations.AddConstraint(model_name='project', constraint=models.UniqueConstraint(fields=('tenant', 'slug'), name='uniq_project_slug_per_tenant')),
        migrations.AddConstraint(model_name='project', constraint=models.UniqueConstraint(fields=('tenant', 'record_id'), name='uniq_project_record_per_tenant')),
    ]
