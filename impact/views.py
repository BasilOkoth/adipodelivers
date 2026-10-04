import re
from functools import wraps
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.utils.text import slugify
from .models import Project, Ward, ProjectImpact, ProjectMedia, SourcePost, TenantMembership
from .post_parser import parse_social_post


def tenant_staff_required(view_func):
    @staff_member_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        if not request.tenant or not TenantMembership.objects.filter(
            tenant=request.tenant, user=request.user, is_active=True,
            role__in=[TenantMembership.Role.OWNER, TenantMembership.Role.ADMIN, TenantMembership.Role.EDITOR]
        ).exists():
            return HttpResponseForbidden('You do not have editing access to this tenant.')
        return view_func(request, *args, **kwargs)
    return wrapped


def _language_mode(request, tenant, allow_bilingual=False):
    requested = (request.GET.get('lang') or '').lower().strip()
    allowed = {'en', 'local'} | ({'bilingual'} if allow_bilingual else set())
    if requested in allowed:
        return requested
    if allow_bilingual and tenant.default_tv_language_mode in allowed:
        return tenant.default_tv_language_mode
    return 'en'


def home(request):
    tenant = request.tenant
    projects = Project.objects.filter(tenant=tenant, published=True).select_related('ward').prefetch_related('media')
    wards = Ward.objects.filter(tenant=tenant)
    lang_mode = _language_mode(request, tenant)
    return render(request, 'impact/home.html', {'tenant': tenant, 'projects': projects, 'wards': wards, 'lang_mode': lang_mode})


def project_detail(request, slug):
    tenant = request.tenant
    p = get_object_or_404(
        Project.objects.select_related('ward').prefetch_related('media', 'impacts', 'documents'),
        tenant=tenant, slug=slug, published=True
    )
    lang_mode = _language_mode(request, tenant)
    return render(request, 'impact/project_detail.html', {'tenant': tenant, 'project': p, 'lang_mode': lang_mode})


def tv(request):
    tenant = request.tenant
    lang_mode = _language_mode(request, tenant, allow_bilingual=True)
    return render(request, 'impact/tv.html', {'tenant': tenant, 'lang_mode': lang_mode})


def re_split_words(value):
    return [x for x in re.split(r'[^A-Za-z0-9]+', value or '') if x]


def _next_record_id(tenant, ward_name, sector):
    prefix = ''.join(x[0] for x in re_split_words(ward_name))[:3].upper() or 'PRJ'
    sector_code = ''.join(x[0] for x in re_split_words(sector))[:3].upper() or 'DEV'
    base = f'{prefix}-{sector_code}'
    n = Project.objects.filter(tenant=tenant, record_id__startswith=base).count() + 1
    candidate = f'{base}-{n:03d}'
    while Project.objects.filter(tenant=tenant, record_id=candidate).exists():
        n += 1
        candidate = f'{base}-{n:03d}'
    return candidate


@tenant_staff_required
@transaction.atomic
def post_to_tv_studio(request):
    tenant = request.tenant
    wards = list(Ward.objects.filter(tenant=tenant))
    preview = None
    original_text = ''
    source_url = ''

    if request.method == 'POST':
        action = request.POST.get('action', 'analyze')
        original_text = request.POST.get('original_text', '').strip()
        source_url = request.POST.get('source_url', '').strip()

        if action == 'analyze':
            if not original_text:
                messages.error(request, 'Paste a post before analysing it.')
            else:
                preview = parse_social_post(original_text, [w.name for w in wards])
                SourcePost.objects.create(
                    tenant=tenant, original_text=original_text, source_url=source_url,
                    parsed_data=preview, created_by=request.user
                )
        elif action in {'save_draft', 'publish'}:
            if not original_text:
                messages.error(request, 'The original post is required.')
            else:
                parsed = parse_social_post(original_text, [w.name for w in wards])
                ward_name = request.POST.get('ward') or parsed.get('ward')
                ward = Ward.objects.filter(tenant=tenant, name=ward_name).first()
                if not ward:
                    messages.error(request, 'Select a valid area/ward before saving.')
                    preview = parsed
                else:
                    sector = request.POST.get('sector', '').strip() or parsed.get('sector') or 'Community Development'
                    title = request.POST.get('title', '').strip() or parsed.get('short_title') or parsed.get('headline')
                    location = request.POST.get('project_location', '').strip() or parsed.get('project_location') or ward.name
                    summary = request.POST.get('summary', '').strip() or parsed.get('summary') or 'Submitted project update.'
                    intervention = request.POST.get('intervention', '').strip() or parsed.get('intervention', '')
                    record_id = _next_record_id(tenant, ward.name, sector)
                    slug = slugify(title)[:165]
                    if Project.objects.filter(tenant=tenant, slug=slug).exists():
                        slug = f'{slug[:155]}-{record_id.lower()}'
                    title_local = request.POST.get('title_local', '').strip()
                    short_title_local = request.POST.get('short_title_local', '').strip() or title_local
                    intervention_local = request.POST.get('intervention_local', '').strip()
                    summary_local = request.POST.get('summary_local', '').strip()
                    location_local = request.POST.get('project_location_local', '').strip()
                    project = Project.objects.create(
                        tenant=tenant, record_id=record_id, slug=slug, title=title[:240], title_local=title_local[:240], short_title=title[:160], short_title_local=short_title_local[:160],
                        ward=ward, sector=sector[:120], intervention=intervention[:240], intervention_local=intervention_local[:240], summary=summary, summary_local=summary_local,
                        project_location=location[:300], project_location_local=location_local[:300], verification_status=Project.Verification.SUBMITTED,
                        source_label='Imported from social post · verification pending', source_url=source_url,
                        tv_enabled=True, published=(action == 'publish'), featured=False,
                    )
                    impacts = request.POST.getlist('impacts') or parsed.get('impacts', [])
                    impact_locals = request.POST.getlist('impacts_local')
                    cleaned_impacts = [x.strip() for x in impacts if x.strip()][:6]
                    for i, text in enumerate(cleaned_impacts):
                        local_text = impact_locals[i].strip() if i < len(impact_locals) else ''
                        ProjectImpact.objects.create(project=project, text=text[:240], text_local=local_text[:240], display_order=i)

                    upload = request.FILES.get('media_file')
                    if upload:
                        media_location = request.POST.get('video_location', '').strip() or location
                        media_location_local = request.POST.get('video_location_local', '').strip()
                        content_type = (getattr(upload, 'content_type', '') or '').lower()
                        media_type = ProjectMedia.MediaType.IMAGE if content_type.startswith('image/') else ProjectMedia.MediaType.VIDEO
                        default_label = 'photo' if media_type == ProjectMedia.MediaType.IMAGE else 'video'
                        ProjectMedia.objects.create(
                            project=project, media_type=media_type,
                            title=request.POST.get('media_title', '').strip() or f'{title} {default_label}',
                            caption=request.POST.get('media_caption', '').strip(), caption_local=request.POST.get('media_caption_local', '').strip(), location_label=media_location[:180], location_label_local=media_location_local[:180],
                            local_file=upload,
                            duration_seconds=int(request.POST.get('duration_seconds') or (12 if media_type == ProjectMedia.MediaType.IMAGE else 15)),
                            tv_enabled=True, show_location_overlay=True, evidence_status=ProjectMedia.Evidence.SUBMITTED,
                        )
                    SourcePost.objects.create(
                        tenant=tenant, original_text=original_text, source_url=source_url, parsed_data=parsed,
                        status=SourcePost.Status.CONVERTED, linked_project=project, created_by=request.user
                    )
                    messages.success(request, f'{record_id} created. {"Published to website/TV." if project.published else "Saved as a draft."}')
                    if action == 'publish':
                        return redirect(project.get_absolute_url())
                    return redirect('post-to-tv-studio')

    return render(request, 'impact/post_to_tv_studio.html', {
        'tenant': tenant, 'wards': wards, 'preview': preview,
        'original_text': original_text, 'source_url': source_url,
        'local_language_name': tenant.secondary_language_name or 'Community language',
        'local_language_short': tenant.secondary_language_short or tenant.secondary_language_name or 'LOCAL',
    })



def tenant_qr(request):
    import io
    import qrcode
    domain = request.tenant.public_domain or request.get_host()
    target = domain if domain.startswith(('http://', 'https://')) else f'https://{domain}'
    img = qrcode.make(target)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return HttpResponse(buf.getvalue(), content_type='image/png')


def tv_playlist_api(request):
    tenant = request.tenant
    lang_mode = _language_mode(request, tenant, allow_bilingual=True)
    items = []
    qs = Project.objects.filter(tenant=tenant, published=True, tv_enabled=True).select_related('ward').prefetch_related('media', 'impacts')
    for p in qs:
        media = []
        for m in p.media.filter(tv_enabled=True):
            url = m.playback_url()
            if not url and m.demo_static_path:
                url = static(m.demo_static_path)
            media.append({
                'id': m.id, 'type': m.media_type, 'title': m.title, 'caption': m.caption,
                'caption_local': m.caption_local, 'url': url, 'hls': m.hls_manifest_url, 'poster': m.poster_url,
                'duration': m.duration_seconds, 'start': m.tv_start_seconds, 'end': m.tv_end_seconds,
                'show_location': m.show_location_overlay, 'location': m.location_label or p.project_location,
                'location_local': m.location_label_local or p.project_location_local,
                'ward': p.ward.name, 'ward_local': p.ward.name_local,
                'lat': str(m.latitude or p.latitude or ''), 'lng': str(m.longitude or p.longitude or ''),
                'evidence': m.evidence_status,
            })
        items.append({
            'id': p.record_id, 'slug': p.slug,
            'title': p.title, 'title_local': p.title_local,
            'short_title': p.short_title or p.title, 'short_title_local': p.short_title_local or p.title_local,
            'ward': p.ward.name, 'ward_local': p.ward.name_local,
            'sector': p.sector, 'location': p.project_location, 'location_local': p.project_location_local,
            'intervention': p.intervention, 'intervention_local': p.intervention_local,
            'summary': p.summary, 'summary_local': p.summary_local,
            'verification': p.verification_status,
            'verification_label': p.get_verification_status_display(),
            'impacts': [{'en': x.text, 'local': x.text_local} for x in p.impacts.all()],
            'url': p.get_absolute_url(), 'media': media,
        })
    brand = {
        'name': tenant.display_name,
        'domain': tenant.public_domain,
        'leader': tenant.leader_name,
        'leader_title': tenant.leader_title,
        'jurisdiction': tenant.jurisdiction_name,
        'county': tenant.county_name,
        'tagline': tenant.tagline,
        'primary_color': tenant.primary_color,
        'accent_color': tenant.accent_color,
    }
    language = {
        'mode': lang_mode,
        'primary_code': tenant.primary_language_code,
        'primary_name': tenant.primary_language_name,
        'secondary_code': tenant.secondary_language_code,
        'secondary_name': tenant.secondary_language_name,
        'secondary_short': tenant.secondary_language_short or tenant.secondary_language_name,
        'bilingual_enabled': tenant.bilingual_tv_enabled,
    }
    return JsonResponse({
        'tenant': tenant.slug, 'brand': brand, 'language': language,
        'wards': [{'en': w.name, 'local': w.name_local} for w in Ward.objects.filter(tenant=tenant)],
        'projects': items,
    })
