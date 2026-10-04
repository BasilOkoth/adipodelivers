from django.contrib import admin
from django.db.models import Q

from .models import (
    Tenant,
    TenantDomain,
    TenantMembership,
    Ward,
    Project,
    ProjectImpact,
    ProjectMedia,
    EvidenceDocument,
    SourcePost,
)


# ============================================================
# ADMIN BRANDING
# ============================================================

admin.site.site_header = "Impact Platform Administration"
admin.site.site_title = "Impact Platform Admin"
admin.site.index_title = "Constituency Impact Management"


# ============================================================
# TENANT ACCESS HELPERS
# ============================================================

def user_is_authenticated(request):
    """
    Safe authentication check.

    Important because Django admin login is rendered while the user
    is still AnonymousUser.
    """
    return bool(
        getattr(request, "user", None)
        and request.user.is_authenticated
    )


def user_has_tenant_access(request, tenant=None):
    """
    Returns True when the current user may access a tenant.

    Superusers can access all tenants.
    Ordinary users must have an active TenantMembership.
    """
    if not user_is_authenticated(request):
        return False

    if request.user.is_superuser:
        return True

    tenant = tenant or getattr(request, "tenant", None)

    if not tenant:
        return False

    return TenantMembership.objects.filter(
        tenant=tenant,
        user_id=request.user.pk,
        is_active=True,
    ).exists()


def tenants_for_user(request):
    """
    Queryset containing only tenants accessible by the current user.
    """
    if not user_is_authenticated(request):
        return Tenant.objects.none()

    if request.user.is_superuser:
        return Tenant.objects.all()

    return Tenant.objects.filter(
        memberships__user_id=request.user.pk,
        memberships__is_active=True,
    ).distinct()


# ============================================================
# BASE TENANT-SCOPED ADMIN
# ============================================================

class TenantScopedAdminMixin:
    """
    Base mixin for models belonging to a tenant.

    Override tenant_lookup for models where tenant is reached through
    another relation, e.g. project__tenant.
    """

    tenant_lookup = "tenant"

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if not user_is_authenticated(request):
            return qs.none()

        if request.user.is_superuser:
            return qs

        tenant = getattr(request, "tenant", None)

        if not tenant:
            return qs.none()

        if not user_has_tenant_access(request, tenant):
            return qs.none()

        return qs.filter(**{self.tenant_lookup: tenant})

    def has_module_permission(self, request):
        # This is the method that was causing your /admin/login/ 500.
        if not user_is_authenticated(request):
            return False

        if request.user.is_superuser:
            return True

        return user_has_tenant_access(request)

    def has_view_permission(self, request, obj=None):
        if not user_is_authenticated(request):
            return False

        if request.user.is_superuser:
            return True

        if not user_has_tenant_access(request):
            return False

        if obj is None:
            return True

        return self.object_belongs_to_request_tenant(request, obj)

    def has_change_permission(self, request, obj=None):
        if not user_is_authenticated(request):
            return False

        if request.user.is_superuser:
            return True

        membership = self.get_membership(request)

        if not membership:
            return False

        # Owner / administrator / editor can modify.
        if membership.role not in {"owner", "admin", "editor"}:
            return False

        if obj is None:
            return True

        return self.object_belongs_to_request_tenant(request, obj)

    def has_add_permission(self, request):
        if not user_is_authenticated(request):
            return False

        if request.user.is_superuser:
            return True

        membership = self.get_membership(request)

        return bool(
            membership
            and membership.role in {"owner", "admin", "editor"}
        )

    def has_delete_permission(self, request, obj=None):
        if not user_is_authenticated(request):
            return False

        if request.user.is_superuser:
            return True

        membership = self.get_membership(request)

        # Editors can publish/edit but should not normally delete records.
        if not membership or membership.role not in {"owner", "admin"}:
            return False

        if obj is None:
            return True

        return self.object_belongs_to_request_tenant(request, obj)

    def get_membership(self, request):
        if not user_is_authenticated(request):
            return None

        tenant = getattr(request, "tenant", None)

        if not tenant:
            return None

        return TenantMembership.objects.filter(
            tenant=tenant,
            user_id=request.user.pk,
            is_active=True,
        ).first()

    def object_belongs_to_request_tenant(self, request, obj):
        tenant = getattr(request, "tenant", None)

        if not tenant:
            return False

        # Direct tenant relationship.
        if hasattr(obj, "tenant_id"):
            return obj.tenant_id == tenant.id

        # Models such as ProjectMedia/EvidenceDocument.
        if hasattr(obj, "project") and obj.project:
            return obj.project.tenant_id == tenant.id

        return False


# ============================================================
# PROJECT INLINES
# ============================================================

class ImpactInline(admin.TabularInline):
    model = ProjectImpact
    extra = 1

    fields = (
        "statement",
        "statement_local",
        "display_order",
    )


class MediaInline(admin.StackedInline):
    model = ProjectMedia
    extra = 0

    fieldsets = (
        (
            "Media",
            {
                "fields": (
                    "media_type",
                    "title",
                    "title_local",
                    "file",
                    "video_url",
                    "thumbnail",
                )
            },
        ),
        (
            "Location",
            {
                "fields": (
                    "location_label",
                    "location_label_local",
                    "latitude",
                    "longitude",
                )
            },
        ),
        (
            "Television",
            {
                "fields": (
                    "tv_enabled",
                    "display_order",
                    "evidence_status",
                )
            },
        ),
    )


class EvidenceInline(admin.TabularInline):
    model = EvidenceDocument
    extra = 0

    fields = (
        "title",
        "source_organization",
        "document",
        "verified",
    )


# ============================================================
# TENANT ADMIN
# ============================================================

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "slug",
        "public_domain",
        "is_active",
        "is_default",
    )

    list_filter = (
        "is_active",
        "is_default",
    )

    search_fields = (
        "name",
        "public_name",
        "slug",
        "public_domain",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if not user_is_authenticated(request):
            return qs.none()

        if request.user.is_superuser:
            return qs

        return qs.filter(
            memberships__user_id=request.user.pk,
            memberships__is_active=True,
        ).distinct()

    def has_module_permission(self, request):
        return user_is_authenticated(request)

    def has_add_permission(self, request):
        # Only platform superusers should create new tenants from Django admin.
        return bool(
            user_is_authenticated(request)
            and request.user.is_superuser
        )

    def has_delete_permission(self, request, obj=None):
        return bool(
            user_is_authenticated(request)
            and request.user.is_superuser
        )


# ============================================================
# TENANT DOMAINS
# ============================================================

@admin.register(TenantDomain)
class TenantDomainAdmin(admin.ModelAdmin):
    list_display = (
        "domain",
        "tenant",
        "is_primary",
    )

    list_filter = (
        "is_primary",
    )

    search_fields = (
        "domain",
        "tenant__name",
        "tenant__public_name",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if not user_is_authenticated(request):
            return qs.none()

        if request.user.is_superuser:
            return qs

        return qs.filter(
            tenant__memberships__user_id=request.user.pk,
            tenant__memberships__is_active=True,
        ).distinct()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (
            db_field.name == "tenant"
            and user_is_authenticated(request)
            and not request.user.is_superuser
        ):
            kwargs["queryset"] = tenants_for_user(request)

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs,
        )

    def has_module_permission(self, request):
        return user_is_authenticated(request)


# ============================================================
# TENANT MEMBERSHIPS
# ============================================================

@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "tenant",
        "role",
        "is_active",
    )

    list_filter = (
        "tenant",
        "role",
        "is_active",
    )

    search_fields = (
        "user__username",
        "user__email",
        "tenant__name",
        "tenant__public_name",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if not user_is_authenticated(request):
            return qs.none()

        if request.user.is_superuser:
            return qs

        return qs.filter(
            tenant__memberships__user_id=request.user.pk,
            tenant__memberships__is_active=True,
        ).distinct()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (
            db_field.name == "tenant"
            and user_is_authenticated(request)
            and not request.user.is_superuser
        ):
            kwargs["queryset"] = tenants_for_user(request)

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs,
        )

    def has_module_permission(self, request):
        return user_is_authenticated(request)

    def has_add_permission(self, request):
        if not user_is_authenticated(request):
            return False

        if request.user.is_superuser:
            return True

        tenant = getattr(request, "tenant", None)

        if not tenant:
            return False

        return TenantMembership.objects.filter(
            tenant=tenant,
            user_id=request.user.pk,
            is_active=True,
            role__in=["owner", "admin"],
        ).exists()


# ============================================================
# PROJECTS
# ============================================================

@admin.register(Project)
class ProjectAdmin(TenantScopedAdminMixin, admin.ModelAdmin):

    list_display = (
        "record_id",
        "short_title",
        "ward",
        "sector",
        "verification_status",
        "tv_enabled",
        "published",
    )

    list_filter = (
        "ward",
        "sector",
        "verification_status",
        "tv_enabled",
        "published",
    )

    search_fields = (
        "record_id",
        "title",
        "title_local",
        "short_title",
        "project_location",
        "project_location_local",
    )

    prepopulated_fields = {
        "slug": ("short_title",)
    }

    inlines = [
        ImpactInline,
        MediaInline,
        EvidenceInline,
    ]

    fieldsets = (
        (
            "Project identity",
            {
                "fields": (
                    "tenant",
                    "record_id",
                    "title",
                    "title_local",
                    "short_title",
                    "slug",
                    "sector",
                    "ward",
                )
            },
        ),
        (
            "Location",
            {
                "fields": (
                    "project_location",
                    "project_location_local",
                    "latitude",
                    "longitude",
                )
            },
        ),
        (
            "Project story",
            {
                "fields": (
                    "summary",
                    "summary_local",
                    "intervention",
                    "intervention_local",
                )
            },
        ),
        (
            "Verification & publishing",
            {
                "fields": (
                    "verification_status",
                    "tv_enabled",
                    "published",
                )
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if (
            not obj.tenant_id
            and getattr(request, "tenant", None)
        ):
            obj.tenant = request.tenant

        super().save_model(
            request,
            obj,
            form,
            change,
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        tenant = getattr(request, "tenant", None)

        if db_field.name == "tenant":
            if (
                user_is_authenticated(request)
                and not request.user.is_superuser
            ):
                kwargs["queryset"] = tenants_for_user(request)

        if db_field.name == "ward":
            if (
                tenant
                and user_is_authenticated(request)
                and not request.user.is_superuser
            ):
                kwargs["queryset"] = Ward.objects.filter(
                    tenant=tenant
                )

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs,
        )


# ============================================================
# WARDS / LOCAL AREAS
# ============================================================

@admin.register(Ward)
class WardAdmin(TenantScopedAdminMixin, admin.ModelAdmin):

    list_display = (
        "name",
        "display_order",
        "tenant",
    )

    list_filter = (
        "tenant",
    )

    search_fields = (
        "name",
        "name_local",
    )

    ordering = (
        "display_order",
        "name",
    )

    def save_model(self, request, obj, form, change):
        if (
            not obj.tenant_id
            and getattr(request, "tenant", None)
        ):
            obj.tenant = request.tenant

        super().save_model(
            request,
            obj,
            form,
            change,
        )


# ============================================================
# POST-TO-TV SOURCE POSTS
# ============================================================

@admin.register(SourcePost)
class SourcePostAdmin(TenantScopedAdminMixin, admin.ModelAdmin):

    list_display = (
        "id",
        "source_platform",
        "status",
        "linked_project",
        "created_by",
        "created_at",
    )

    list_filter = (
        "source_platform",
        "status",
        "created_at",
    )

    search_fields = (
        "original_text",
        "source_url",
        "linked_project__title",
    )

    readonly_fields = (
        "parsed_data",
        "created_at",
        "updated_at",
    )

    date_hierarchy = "created_at"


# ============================================================
# MEDIA
# ============================================================

@admin.register(ProjectMedia)
class ProjectMediaAdmin(
    TenantScopedAdminMixin,
    admin.ModelAdmin,
):
    tenant_lookup = "project__tenant"

    list_display = (
        "title",
        "project",
        "media_type",
        "location_label",
        "evidence_status",
        "tv_enabled",
    )

    list_filter = (
        "media_type",
        "evidence_status",
        "tv_enabled",
    )

    search_fields = (
        "title",
        "title_local",
        "location_label",
        "location_label_local",
        "project__title",
        "project__record_id",
    )

    def formfield_for_foreignkey(
        self,
        db_field,
        request,
        **kwargs,
    ):
        tenant = getattr(request, "tenant", None)

        if (
            db_field.name == "project"
            and tenant
            and user_is_authenticated(request)
            and not request.user.is_superuser
        ):
            kwargs["queryset"] = Project.objects.filter(
                tenant=tenant
            )

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs,
        )


# ============================================================
# EVIDENCE
# ============================================================

@admin.register(EvidenceDocument)
class EvidenceDocumentAdmin(
    TenantScopedAdminMixin,
    admin.ModelAdmin,
):
    tenant_lookup = "project__tenant"

    list_display = (
        "title",
        "project",
        "source_organization",
        "verified",
        "uploaded_at",
    )

    list_filter = (
        "verified",
        "uploaded_at",
    )

    search_fields = (
        "title",
        "source_organization",
        "project__title",
        "project__record_id",
    )

    def formfield_for_foreignkey(
        self,
        db_field,
        request,
        **kwargs,
    ):
        tenant = getattr(request, "tenant", None)

        if (
            db_field.name == "project"
            and tenant
            and user_is_authenticated(request)
            and not request.user.is_superuser
        ):
            kwargs["queryset"] = Project.objects.filter(
                tenant=tenant
            )

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs,
        )
