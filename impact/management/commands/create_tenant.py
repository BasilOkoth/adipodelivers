from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from impact.models import Tenant, TenantDomain, TenantMembership, Ward


class Command(BaseCommand):
    help = 'Create a new branded tenant/client without cloning the codebase.'

    def add_arguments(self, parser):
        parser.add_argument('name')
        parser.add_argument('--slug')
        parser.add_argument('--domain', required=True)
        parser.add_argument('--leader', default='')
        parser.add_argument('--title', default='Public Office')
        parser.add_argument('--jurisdiction', default='')
        parser.add_argument('--county', default='')
        parser.add_argument('--areas', default='', help='Comma-separated wards/areas to create')
        parser.add_argument('--area-unit', default='ward')
        parser.add_argument('--owner-username', default='', help='Existing Django username to make tenant owner')
        parser.add_argument('--secondary-language', default='', help='Community language name, e.g. Dholuo')
        parser.add_argument('--secondary-language-code', default='', help='Language code, e.g. luo')
        parser.add_argument('--secondary-language-short', default='', help='Short UI label, e.g. DHO')
        parser.add_argument('--bilingual-tv', action='store_true', help='Enable bilingual TV mode')

    def handle(self, *args, **o):
        slug = o['slug'] or slugify(o['name'])[:80]
        domain = o['domain'].lower().replace('https://', '').replace('http://', '').strip('/').split(':')[0]
        if Tenant.objects.filter(slug=slug).exists():
            raise CommandError(f'Tenant slug {slug!r} already exists.')
        if TenantDomain.objects.filter(domain=domain).exists():
            raise CommandError(f'Domain {domain!r} is already assigned.')
        tenant = Tenant.objects.create(
            name=o['name'], public_name=o['name'], slug=slug, public_domain=domain,
            leader_name=o['leader'], leader_title=o['title'], jurisdiction_name=o['jurisdiction'],
            county_name=o['county'], area_unit_singular=o['area_unit'], area_unit_plural=f"{o['area_unit']}s",
            secondary_language_name=o['secondary_language'], secondary_language_code=o['secondary_language_code'],
            secondary_language_short=o['secondary_language_short'], bilingual_tv_enabled=o['bilingual_tv'],
            default_tv_language_mode='bilingual' if o['bilingual_tv'] and o['secondary_language'] else 'en',
            brand_mark=(o['name'][:1] or 'I').upper(), is_active=True,
        )
        TenantDomain.objects.create(tenant=tenant, domain=domain, is_primary=True)
        for i, area in enumerate([x.strip() for x in o['areas'].split(',') if x.strip()]):
            Ward.objects.create(tenant=tenant, name=area, display_order=i)
        if o['owner_username']:
            User = get_user_model()
            try:
                user = User.objects.get(username=o['owner_username'])
            except User.DoesNotExist:
                raise CommandError(f"User {o['owner_username']!r} does not exist; create the user first.")
            TenantMembership.objects.update_or_create(tenant=tenant, user=user, defaults={'role':'owner','is_active':True})
        self.stdout.write(self.style.SUCCESS(f'Created tenant {tenant.slug} for {domain}.'))
