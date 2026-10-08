from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('impact', '0007_premium_project_studio'),
    ]

    operations = [
        migrations.CreateModel(
            name='BursaryWardSummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reporting_period', models.CharField(default='2026', max_length=40)),
                ('students_supported', models.PositiveIntegerField(default=0)),
                ('amount_allocated', models.DecimalField(blank=True, decimal_places=2, max_digits=16, null=True)),
                ('secondary_count', models.PositiveIntegerField(default=0)),
                ('college_tvet_count', models.PositiveIntegerField(default=0)),
                ('university_count', models.PositiveIntegerField(default=0)),
                ('female_count', models.PositiveIntegerField(default=0)),
                ('male_count', models.PositiveIntegerField(default=0)),
                ('notes', models.CharField(blank=True, max_length=240)),
                ('verified', models.BooleanField(default=False)),
                ('tv_enabled', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bursary_summaries', to='impact.tenant')),
                ('ward', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bursary_summaries', to='impact.ward')),
            ],
            options={
                'ordering': ['ward__display_order', 'ward__name'],
                'unique_together': {('tenant', 'ward', 'reporting_period')},
            },
        ),
    ]
