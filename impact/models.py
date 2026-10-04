from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify




def project_media_upload_to(instance, filename):
    tenant_slug = instance.project.tenant.slug if instance.project_id else 'unassigned'
    return f'tenants/{tenant_slug}/originals/{instance.project.record_id}/{filename}'


def evidence_upload_to(instance, filename):
    tenant_slug = instance.project.tenant.slug if instance.project_id else 'unassigned'
    return f'tenants/{tenant_slug}/evidence/{instance.project.record_id}/{filename}'

class Tenant(models.Model):
    """One branded deployment/client in the shared platform."""
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=80, unique=True)
    public_name = models.CharField(max_length=180, blank=True)
    tagline = models.CharField(max_length=240, blank=True)
    leader_name = models.CharField(max_length=180, blank=True)
    leader_title = models.CharField(max_length=180, blank=True)
    jurisdiction_name = models.CharField(max_length=180, blank=True)
    county_name = models.CharField(max_length=180, blank=True)
    country_name = models.CharField(max_length=120, default='Kenya')
    public_domain = models.CharField(max_length=255, blank=True)
    brand_mark = models.CharField(max_length=12, default='I')
    primary_color = models.CharField(max_length=20, default='#061421')
    accent_color = models.CharField(max_length=20, default='#e5c176')
    logo = models.ImageField(upload_to='tenant-branding/', blank=True)
    qr_image = models.ImageField(upload_to='tenant-branding/', blank=True)
    area_label = models.CharField(max_length=100, blank=True)
    population_label = models.CharField(max_length=100, blank=True)
    area_unit_singular = models.CharField(max_length=60, default='ward')
    area_unit_plural = models.CharField(max_length=60, default='wards')
    primary_language_code = models.CharField(max_length=12, default='en')
    primary_language_name = models.CharField(max_length=60, default='English')
    secondary_language_code = models.CharField(max_length=12, blank=True)
    secondary_language_name = models.CharField(max_length=60, blank=True)
    secondary_language_short = models.CharField(max_length=12, blank=True)
    bilingual_tv_enabled = models.BooleanField(default=False)
    default_tv_language_mode = models.CharField(max_length=16, choices=[('en','English'),('local','Community language'),('bilingual','Bilingual')], default='en')
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.public_name or self.name

    @property
    def display_name(self):
        return self.public_name or self.name


class TenantDomain(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='domains')
    domain = models.CharField(max_length=255, unique=True, help_text='Hostname only, e.g. adipodelivers.org')
    is_primary = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.domain = self.domain.lower().strip().split(':')[0]
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.domain} → {self.tenant}'


class TenantMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        ADMIN = 'admin', 'Administrator'
        EDITOR = 'editor', 'Editor'
        VIEWER = 'viewer', 'Viewer'

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tenant_memberships')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EDITOR)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [('tenant', 'user')]

    def __str__(self):
        return f'{self.user} · {self.tenant} · {self.get_role_display()}'


class Ward(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='wards')
    name = models.CharField(max_length=120)
    name_local = models.CharField(max_length=120, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    def __str__(self): return self.name

    class Meta:
        ordering = ['display_order', 'name']
        unique_together = [('tenant', 'name')]


class Project(models.Model):
    class Verification(models.TextChoices):
        SUBMITTED = 'submitted', 'Submitted · verification pending'
        VERIFIED = 'verified', 'Verified'
        DEMO = 'demo', 'Demo record'

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='projects')
    slug = models.SlugField(max_length=180, blank=True)
    record_id = models.CharField(max_length=50)
    title = models.CharField(max_length=240)
    title_local = models.CharField(max_length=240, blank=True)
    short_title = models.CharField(max_length=160, blank=True)
    short_title_local = models.CharField(max_length=160, blank=True)
    ward = models.ForeignKey(Ward, on_delete=models.PROTECT, related_name='projects')
    sector = models.CharField(max_length=120)
    intervention = models.CharField(max_length=240, blank=True)
    intervention_local = models.CharField(max_length=240, blank=True)
    summary = models.TextField()
    summary_local = models.TextField(blank=True)
    project_location = models.CharField(max_length=300, help_text='Human-readable project location or route')
    project_location_local = models.CharField(max_length=300, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    funding_source = models.CharField(max_length=180, blank=True)
    implementing_agency = models.CharField(max_length=180, blank=True)
    beneficiaries = models.PositiveIntegerField(null=True, blank=True)
    verification_status = models.CharField(max_length=20, choices=Verification.choices, default=Verification.SUBMITTED)
    source_label = models.CharField(max_length=180, blank=True)
    source_url = models.URLField(blank=True)
    tv_enabled = models.BooleanField(default=True)
    published = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.ward_id and not self.tenant_id:
            self.tenant_id = self.ward.tenant_id
        if not self.slug:
            self.slug = slugify(self.short_title or self.title)[:170]
        super().save(*args, **kwargs)

    def get_absolute_url(self): return reverse('project-detail', args=[self.slug])
    def __str__(self): return self.title

    class Meta:
        ordering = ['-featured', '-updated_at']
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'slug'], name='uniq_project_slug_per_tenant'),
            models.UniqueConstraint(fields=['tenant', 'record_id'], name='uniq_project_record_per_tenant'),
        ]


class ProjectImpact(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='impacts')
    text = models.CharField(max_length=240)
    text_local = models.CharField(max_length=240, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    class Meta: ordering = ['display_order', 'id']
    def __str__(self): return self.text


class ProjectMedia(models.Model):
    class MediaType(models.TextChoices):
        VIDEO = 'video', 'Video'
        IMAGE = 'image', 'Image'
    class Evidence(models.TextChoices):
        SUBMITTED = 'submitted', 'Submitted'
        VERIFIED = 'verified', 'Verified'
        DEMO = 'demo', 'Demonstration'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='media')
    media_type = models.CharField(max_length=10, choices=MediaType.choices, default=MediaType.VIDEO)
    title = models.CharField(max_length=180)
    caption = models.CharField(max_length=300, blank=True)
    caption_local = models.CharField(max_length=300, blank=True)
    location_label = models.CharField(max_length=180, blank=True, help_text='Exact media location, e.g. Nyapuodi Beach · West Karachuonyo')
    location_label_local = models.CharField(max_length=180, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    local_file = models.FileField(upload_to=project_media_upload_to, blank=True)
    original_s3_key = models.CharField(max_length=500, blank=True)
    hls_manifest_url = models.URLField(max_length=1000, blank=True)
    mp4_fallback_url = models.URLField(max_length=1000, blank=True)
    poster_url = models.URLField(max_length=1000, blank=True)
    demo_static_path = models.CharField(max_length=300, blank=True)
    duration_seconds = models.PositiveIntegerField(default=15)
    tv_enabled = models.BooleanField(default=True)
    tv_start_seconds = models.PositiveIntegerField(default=0)
    tv_end_seconds = models.PositiveIntegerField(null=True, blank=True)
    show_location_overlay = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    evidence_status = models.CharField(max_length=20, choices=Evidence.choices, default=Evidence.SUBMITTED)

    def playback_url(self):
        if self.hls_manifest_url: return self.hls_manifest_url
        if self.mp4_fallback_url: return self.mp4_fallback_url
        if self.local_file: return self.local_file.url
        return ''

    def __str__(self): return f'{self.project.short_title or self.project.title} — {self.title}'
    class Meta: ordering = ['display_order', 'id']


class EvidenceDocument(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=180)
    file = models.FileField(upload_to=evidence_upload_to, blank=True)
    external_url = models.URLField(blank=True)
    source_organization = models.CharField(max_length=180, blank=True)
    verified = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title


class SourcePost(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        CONVERTED = 'converted', 'Converted to project'

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='source_posts')
    original_text = models.TextField()
    source_url = models.URLField(blank=True)
    source_platform = models.CharField(max_length=40, default='Facebook')
    parsed_data = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    linked_project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='source_posts')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return f'{self.source_platform} import #{self.pk or "new"}'
    class Meta: ordering = ['-created_at']
