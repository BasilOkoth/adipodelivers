from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('impact','0001_initial'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[migrations.CreateModel(
        name='SourcePost',
        fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('original_text',models.TextField()),
            ('source_url',models.URLField(blank=True)),
            ('source_platform',models.CharField(default='Facebook',max_length=40)),
            ('parsed_data',models.JSONField(blank=True,default=dict)),
            ('status',models.CharField(choices=[('draft','Draft'),('converted','Converted to project')],default='draft',max_length=20)),
            ('created_at',models.DateTimeField(auto_now_add=True)),
            ('updated_at',models.DateTimeField(auto_now=True)),
            ('created_by',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,to=settings.AUTH_USER_MODEL)),
            ('linked_project',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='source_posts',to='impact.project')),
        ],
        options={'ordering':['-created_at']},
    )]
