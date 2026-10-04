from django.conf import settings
from django.http import Http404
from .models import Tenant, TenantDomain


class TenantResolutionMiddleware:
    """Resolve request.tenant from hostname. In DEBUG, ?tenant=<slug> can switch tenants."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = None
        debug_slug = request.GET.get('tenant') if settings.DEBUG else None
        if debug_slug:
            tenant = Tenant.objects.filter(slug=debug_slug, is_active=True).first()
            if tenant:
                request.session['debug_tenant_slug'] = tenant.slug
        elif settings.DEBUG and request.session.get('debug_tenant_slug'):
            tenant = Tenant.objects.filter(slug=request.session['debug_tenant_slug'], is_active=True).first()

        if not tenant:
            host = request.get_host().split(':')[0].lower()
            mapping = TenantDomain.objects.select_related('tenant').filter(domain=host, tenant__is_active=True).first()
            tenant = mapping.tenant if mapping else None

        if not tenant:
            tenant = Tenant.objects.filter(is_default=True, is_active=True).first()
        if not tenant:
            tenant = Tenant.objects.filter(is_active=True).first()

        if not tenant and not request.path.startswith('/admin/'):
            raise Http404('No active tenant is configured for this domain.')

        request.tenant = tenant
        return self.get_response(request)
