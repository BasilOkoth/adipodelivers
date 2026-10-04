from django.contrib import admin
from .models import (
    Tenant, TenantDomain, TenantMembership, Ward, Project, ProjectImpact,
    ProjectMedia, EvidenceDocument, SourcePost
)


class TenantScopedAdminMixin:
    tenant_lookup = 'tenant'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or not getattr(request, 'tenant', None):
            return qs
        return qs.filter(**{self.tenant_lookup: request.tenant})

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        tenant = getattr(request, 'tenant', None)
        return bool(tenant and TenantMembership.objects.filter(tenant=tenant, user=request.user, is_active=True).exists())


class ImpactInline(admin.TabularInline):
    model = ProjectImpact
    extra = 1


class MediaInline(admin.StackedInline):
    model = ProjectMedia
    extra = 0


class EvidenceInline(admin.TabularInline):
    model = EvidenceDocument
    extra = 0


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'slug', 'public_domain', 'is_active', 'is_default')
    search_fields = ('name', 'public_name', 'slug', 'public_domain')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(memberships__user=request.user, memberships__is_active=True).distinct()


@admin.register(TenantDomain)
class TenantDomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant', 'is_primary')
    list_filter = ('is_primary',)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser: return qs
        return qs.filter(tenant__memberships__user=request.user, tenant__memberships__is_active=True).distinct()
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'tenant' and not request.user.is_superuser:
            kwargs['queryset'] = Tenant.objects.filter(memberships__user=request.user, memberships__is_active=True).distinct()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'tenant', 'role', 'is_active')
    list_filter = ('tenant', 'role', 'is_active')
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser: return qs
        return qs.filter(tenant__memberships__user=request.user, tenant__memberships__is_active=True).distinct()
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'tenant' and not request.user.is_superuser:
            kwargs['queryset'] = Tenant.objects.filter(memberships__user=request.user, memberships__is_active=True).distinct()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Project)
class ProjectAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ('record_id', 'short_title', 'ward', 'sector', 'verification_status', 'tv_enabled', 'published')
    list_filter = ('ward', 'sector', 'verification_status', 'tv_enabled', 'published')
    search_fields = ('record_id', 'title', 'short_title', 'project_location')
    prepopulated_fields = {'slug': ('short_title',)}
    inlines = [ImpactInline, MediaInline, EvidenceInline]

    def save_model(self, request, obj, form, change):
        if not obj.tenant_id and getattr(request, 'tenant', None):
            obj.tenant = request.tenant
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'ward' and getattr(request, 'tenant', None) and not request.user.is_superuser:
            kwargs['queryset'] = Ward.objects.filter(tenant=request.tenant)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Ward)
class WardAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'display_order', 'tenant')

    def save_model(self, request, obj, form, change):
        if not obj.tenant_id and getattr(request, 'tenant', None):
            obj.tenant = request.tenant
        super().save_model(request, obj, form, change)


@admin.register(SourcePost)
class SourcePostAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'source_platform', 'status', 'linked_project', 'created_by', 'created_at')
    list_filter = ('source_platform', 'status', 'created_at')
    search_fields = ('original_text', 'source_url', 'linked_project__title')
    readonly_fields = ('parsed_data', 'created_at', 'updated_at')


@admin.register(ProjectMedia)
class ProjectMediaAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    tenant_lookup = 'project__tenant'
    list_display = ('title', 'project', 'media_type', 'location_label', 'evidence_status', 'tv_enabled')


@admin.register(EvidenceDocument)
class EvidenceDocumentAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    tenant_lookup = 'project__tenant'
    list_display = ('title', 'project', 'source_organization', 'verified', 'uploaded_at')
