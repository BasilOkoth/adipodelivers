from django.core.management.base import BaseCommand
from impact.models import Tenant, TenantDomain, Ward, Project, ProjectImpact, ProjectMedia


class Command(BaseCommand):
    help = 'Create starter AdipoDelivers records only when they do not already exist. Safe to run repeatedly.'

    def handle(self, *args, **opts):
        tenant, tenant_created = Tenant.objects.get_or_create(slug='adipodelivers', defaults={
            'name': 'AdipoDelivers', 'public_name': 'Karachuonyo Impact',
            'tagline': 'Public service, made visible.', 'leader_name': 'Hon. Andrew Adipo Okuome',
            'leader_title': 'Member of Parliament', 'jurisdiction_name': 'Karachuonyo Constituency',
            'county_name': 'Homa Bay County', 'country_name': 'Kenya', 'public_domain': 'adipodelivers.org',
            'brand_mark': 'AD', 'primary_color': '#0b0908', 'accent_color': '#d7232f',
            'area_label': '441.2 km²', 'population_label': '178,686 · 2019',
            'area_unit_singular': 'ward', 'area_unit_plural': 'wards', 'is_active': True, 'is_default': True,
        })
        TenantDomain.objects.get_or_create(tenant=tenant, domain='adipodelivers.org', defaults={'is_primary': True})
        TenantDomain.objects.get_or_create(tenant=tenant, domain='www.adipodelivers.org')

        names = ['Wang’chieng', 'Kendu Bay Town', 'Kanyaluo', 'Central Karachuonyo', 'North Karachuonyo', 'West Karachuonyo', 'Kibiri']
        wards = {}
        for i, name in enumerate(names):
            wards[name], created = Ward.objects.get_or_create(tenant=tenant, name=name, defaults={'display_order': i})

        road, road_created = Project.objects.get_or_create(tenant=tenant, record_id='WEST-ROAD-001', defaults={
            'slug': 'west-karachuonyo-new-road-connection',
            'title': 'Alara–Angang Market–Nyapuodi Beach–Kisindi Ndere Junction–Kaimbo Beach Road',
            'short_title': 'West Karachuonyo New Road Connection', 'ward': wards['West Karachuonyo'],
            'sector': 'Roads & Connectivity', 'intervention': 'Opening and grading of a new road connection',
            'summary': 'A new road corridor opening and grading project improving connectivity between communities, beaches, markets and local economic centres.',
            'project_location': 'Alara → Angang Market → Nyapuodi Beach → Kisindi Ndere Junction → Kaimbo Beach',
            'verification_status': 'submitted', 'source_label': 'Starter record', 'entry_source': 'seeded', 'story_priority': 'flagship',
            'tv_enabled': True, 'published': True, 'featured': True,
        })
        if road_created:
            for i, text in enumerate([
                'Improved local connectivity', 'Easier access to markets', 'Support for traders and farmers',
                'Improved access to beaches and businesses', 'Potential to stimulate local economic activity'
            ]):
                ProjectImpact.objects.create(project=road, text=text, display_order=i)
            ProjectMedia.objects.create(
                project=road, title='Road story preview', caption='New community road connection',
                location_label='West Karachuonyo Ward · project route', demo_static_path='impact/media/road-demo.mp4',
                duration_seconds=16, tv_enabled=True, tv_start_seconds=0, tv_end_seconds=16,
                show_location_overlay=False, evidence_status='demo'
            )

        school, school_created = Project.objects.get_or_create(tenant=tenant, record_id='WANG-EDU-001', defaults={
            'slug': 'kogweno-primary-school-classroom-upgrade',
            'title': 'Classroom Infrastructure Upgrade at Kogweno Primary School',
            'short_title': 'Kogweno Primary School Classroom Upgrade', 'ward': wards['Wang’chieng'],
            'sector': 'Education Infrastructure', 'intervention': 'Upgrade and renovation of classroom infrastructure',
            'summary': 'Classroom infrastructure improvements at Kogweno Primary School supporting a safer, more comfortable and conducive learning environment.',
            'project_location': 'Kogweno Primary School · Wang’chieng Ward · Karachuonyo Constituency',
            'latitude': -0.363910, 'longitude': 34.746320, 'verification_status': 'submitted',
            'source_label': 'Starter record', 'entry_source': 'seeded', 'story_priority': 'flagship',
            'tv_enabled': True, 'published': True, 'featured': True,
        })
        if school_created:
            for i, text in enumerate([
                'Safer and more comfortable classrooms for learners', 'Improved learning environment',
                'Stronger education infrastructure for the school community'
            ]):
                ProjectImpact.objects.create(project=school, text=text, display_order=i)
            ProjectMedia.objects.create(
                project=school, media_type=ProjectMedia.MediaType.IMAGE,
                title='Kogweno Primary School classroom block',
                caption='Upgraded classroom block at Kogweno Primary School.',
                location_label='Kogweno Primary School · Wang’chieng Ward',
                latitude=-0.363910, longitude=34.746320,
                demo_static_path='impact/media/kogweno-primary-school.jpg', duration_seconds=12,
                tv_enabled=True, show_location_overlay=False, evidence_status='submitted', is_cover=True,
            )

        created_bits = []
        if tenant_created: created_bits.append('tenant')
        if road_created: created_bits.append('road starter')
        if school_created: created_bits.append('school starter')
        if created_bits:
            self.stdout.write(self.style.SUCCESS('Created: ' + ', '.join(created_bits)))
        else:
            self.stdout.write(self.style.WARNING('No starter data changed. Existing production records were preserved.'))
