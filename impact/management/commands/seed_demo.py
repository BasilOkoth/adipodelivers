from django.core.management.base import BaseCommand
from impact.models import Tenant, TenantDomain, Ward, Project, ProjectImpact, ProjectMedia


class Command(BaseCommand):
    help = 'Seed the AdipoDelivers tenant and its two submitted demonstration records.'

    def handle(self, *args, **opts):
        tenant, _ = Tenant.objects.update_or_create(slug='adipodelivers', defaults={
            'name': 'AdipoDelivers', 'public_name': 'Karachuonyo Impact',
            'tagline': 'Public service, made visible.', 'leader_name': 'Hon. Andrew Adipo Okuome',
            'leader_title': 'Member of Parliament', 'jurisdiction_name': 'Karachuonyo Constituency',
            'county_name': 'Homa Bay County', 'country_name': 'Kenya', 'public_domain': 'adipodelivers.org',
            'brand_mark': 'K', 'primary_color': '#061421', 'accent_color': '#e5c176',
            'area_label': '441.2 km²', 'population_label': '178,686 · 2019',
            'area_unit_singular': 'ward', 'area_unit_plural': 'wards', 'is_active': True, 'is_default': True,
        })
        TenantDomain.objects.get_or_create(tenant=tenant, domain='adipodelivers.org', defaults={'is_primary': True})
        TenantDomain.objects.get_or_create(tenant=tenant, domain='www.adipodelivers.org')

        names = ['Wang’chieng', 'Kendu Bay Town', 'Kanyaluo', 'Central Karachuonyo', 'North Karachuonyo', 'West Karachuonyo', 'Kibiri']
        wards = {}
        for i, n in enumerate(names):
            wards[n], _ = Ward.objects.update_or_create(tenant=tenant, name=n, defaults={'display_order': i})

        p, _ = Project.objects.update_or_create(tenant=tenant, record_id='WEST-ROAD-001', defaults={
            'slug': 'west-karachuonyo-new-road-connection',
            'title': 'Alara–Angang Market–Nyapuodi Beach–Kisindi Ndere Junction–Kaimbo Beach Road',
            'short_title': 'West Karachuonyo New Road Connection', 'ward': wards['West Karachuonyo'],
            'sector': 'Roads & Connectivity', 'intervention': 'Opening and grading of a new road connection',
            'summary': 'A submitted project record describing the opening and grading of a new road corridor intended to improve movement between communities, beaches, markets and local economic centres.',
            'project_location': 'Alara → Angang Market → Nyapuodi Beach → Kisindi Ndere Junction → Kaimbo Beach',
            'verification_status': 'submitted', 'source_label': 'Submitted project update',
            'tv_enabled': True, 'published': True, 'featured': True,
        })
        p.impacts.all().delete()
        for i, t in enumerate(['Improved local connectivity', 'Easier access to markets', 'Support for traders and farmers', 'Improved access to beaches and businesses', 'Potential to stimulate local economic activity']):
            ProjectImpact.objects.create(project=p, text=t, display_order=i)
        p.media.all().delete()
        ProjectMedia.objects.create(project=p, title='Road story preview', caption='New community road connection', location_label='West Karachuonyo Ward · project route', demo_static_path='impact/media/road-demo.mp4', duration_seconds=16, tv_enabled=True, tv_start_seconds=0, tv_end_seconds=16, show_location_overlay=True, evidence_status='demo')

        school, _ = Project.objects.update_or_create(tenant=tenant, record_id='WANG-EDU-001', defaults={
            'slug': 'kogweno-primary-school-classroom-upgrade', 'title': 'Classroom Infrastructure Upgrade at Kogweno Primary School',
            'short_title': 'Kogweno Primary School Classroom Upgrade', 'ward': wards['Wang’chieng'],
            'sector': 'Education Infrastructure', 'intervention': 'Upgrade and renovation of classroom infrastructure',
            'summary': 'A submitted project update describing improvements to classroom infrastructure at Kogweno Primary School to support a safer, more comfortable and conducive learning environment.',
            'project_location': 'Kogweno Primary School · Wang’chieng Ward · Karachuonyo Constituency',
            'latitude': -0.363910, 'longitude': 34.746320, 'verification_status': 'submitted',
            'source_label': 'Submitted social post + uploaded project photo · verification pending',
            'tv_enabled': True, 'published': True, 'featured': True,
        })
        school.impacts.all().delete()
        for i, t in enumerate(['Safer and more comfortable classrooms for learners', 'Improved learning environment', 'Stronger education infrastructure for the school community']):
            ProjectImpact.objects.create(project=school, text=t, display_order=i)
        school.media.all().delete()
        ProjectMedia.objects.create(project=school, media_type=ProjectMedia.MediaType.IMAGE, title='Kogweno Primary School classroom block', caption='Submitted project photograph showing the upgraded classroom block.', location_label='Kogweno Primary School · Wang’chieng Ward', latitude=-0.363910, longitude=34.746320, demo_static_path='impact/media/kogweno-primary-school.jpg', duration_seconds=12, tv_enabled=True, show_location_overlay=True, evidence_status='submitted')
        self.stdout.write(self.style.SUCCESS('Seeded tenant adipodelivers with WEST-ROAD-001 and WANG-EDU-001.'))
