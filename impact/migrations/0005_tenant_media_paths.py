from django.db import migrations, models
import impact.models

class Migration(migrations.Migration):
    dependencies = [('impact', '0004_bilingual_content')]
    operations = [
        migrations.AlterField(
            model_name='projectmedia',
            name='local_file',
            field=models.FileField(blank=True, upload_to=impact.models.project_media_upload_to),
        ),
        migrations.AlterField(
            model_name='evidencedocument',
            name='file',
            field=models.FileField(blank=True, upload_to=impact.models.evidence_upload_to),
        ),
    ]
