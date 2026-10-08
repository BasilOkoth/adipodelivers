import re
from functools import wraps
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.utils.text import slugify
from .models import Project, Ward, ProjectImpact, ProjectMedia, EvidenceDocument, SourcePost, TenantMembership, BursaryWardSummary
from .forms import ProjectForm, ProjectMediaForm, ProjectMediaBatchForm, EvidenceForm, WardForm, TenantBrandForm, TenantTVSettingsForm, BursaryWardSummaryForm
from .post_parser import parse_social_post


def tenant_staff_required(view_func):
    @login_required(login_url='control-login')
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        tenant = getattr(request, 'tenant', None)
        if not tenant or not TenantMembership.objects.filter(
            tenant=tenant, user_id=request.user.pk, is_active=True,
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
                        source_label='Imported from public update', source_url=source_url, entry_source=Project.EntrySource.IMPORTED,
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
            'budget': str(p.budget) if p.budget is not None else '',
            'funding_source': p.funding_source,
            'implementing_agency': p.implementing_agency,
            'beneficiaries': p.beneficiaries or '',
            'start_date': p.start_date.isoformat() if p.start_date else '',
            'completion_date': p.completion_date.isoformat() if p.completion_date else '',
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
        'leader_photo': tenant.leader_photo.url if tenant.leader_photo else '',
        'logo': tenant.logo.url if tenant.logo else '',
        'tv_intro_kicker': tenant.tv_intro_kicker,
        'tv_intro_headline': tenant.tv_intro_headline,
        'tv_intro_subheadline': tenant.tv_intro_subheadline,
        'tv_ticker_text': tenant.tv_ticker_text,
        'tv_show_leader_photo': tenant.tv_show_leader_photo,
        'tv_show_qr': tenant.tv_show_qr,
        'tv_show_clock': tenant.tv_show_clock,
        'tv_show_ticker': tenant.tv_show_ticker,
        'tv_show_website': tenant.tv_show_website,
        'tv_show_project_status': tenant.tv_show_project_status,
        'tv_intro_duration_seconds': tenant.tv_intro_duration_seconds,
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

    bursary_qs = BursaryWardSummary.objects.filter(
        tenant=tenant, verified=True, tv_enabled=True
    ).select_related('ward').order_by('ward__display_order', 'ward__name')
    totals = bursary_qs.aggregate(
        students=Sum('students_supported'),
        amount=Sum('amount_allocated'),
        secondary=Sum('secondary_count'),
        college_tvet=Sum('college_tvet_count'),
        university=Sum('university_count'),
        female=Sum('female_count'),
        male=Sum('male_count'),
    )
    bursary_data = {
        'students': totals['students'] or 0,
        'amount': str(totals['amount'] or 0),
        'secondary': totals['secondary'] or 0,
        'college_tvet': totals['college_tvet'] or 0,
        'university': totals['university'] or 0,
        'female': totals['female'] or 0,
        'male': totals['male'] or 0,
        'wards_reached': bursary_qs.values('ward_id').distinct().count(),
        'periods': list(bursary_qs.values_list('reporting_period', flat=True).distinct()),
        'wards': [{
            'ward': x.ward.name,
            'ward_local': x.ward.name_local,
            'period': x.reporting_period,
            'students': x.students_supported,
            'amount': str(x.amount_allocated or 0),
            'secondary': x.secondary_count,
            'college_tvet': x.college_tvet_count,
            'university': x.university_count,
            'female': x.female_count,
            'male': x.male_count,
            'note': x.notes,
        } for x in bursary_qs],
    }

    return JsonResponse({
        'tenant': tenant.slug, 'brand': brand, 'language': language,
        'wards': [{'en': w.name, 'local': w.name_local} for w in Ward.objects.filter(tenant=tenant)],
        'projects': items,
        'bursary': bursary_data,
    })


# ============================================================
# CUSTOM CONTROL CENTRE — separate from Django admin
# ============================================================

def control_login(request):
    if request.user.is_authenticated:
        return redirect('control-dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, 'Invalid username or password.')
        else:
            tenant = getattr(request, 'tenant', None)
            allowed = user.is_superuser or (tenant and TenantMembership.objects.filter(
                tenant=tenant, user_id=user.pk, is_active=True
            ).exists())
            if not allowed:
                messages.error(request, 'This account does not have access to this workspace.')
            else:
                login(request, user)
                return redirect(request.GET.get('next') or 'control-dashboard')
    return render(request, 'impact/control/login.html', {'tenant': request.tenant})


def control_logout(request):
    logout(request)
    return redirect('control-login')


def _dashboard_context(request, **extra):
    tenant = request.tenant
    projects = Project.objects.filter(tenant=tenant)
    media = ProjectMedia.objects.filter(project__tenant=tenant)
    evidence = EvidenceDocument.objects.filter(project__tenant=tenant)
    ctx = {
        'tenant': tenant,
        'project_count': projects.count(),
        'published_count': projects.filter(published=True).count(),
        'tv_count': projects.filter(tv_enabled=True, published=True).count(),
        'verification_count': projects.filter(verification_status=Project.Verification.SUBMITTED).count(),
        'media_count': media.count(),
        'evidence_count': evidence.count(),
        'ward_count': Ward.objects.filter(tenant=tenant).count(),
        'source_post_count': SourcePost.objects.filter(tenant=tenant).count(),
    }
    ctx.update(extra)
    return ctx


@tenant_staff_required
def control_dashboard(request):
    tenant = request.tenant
    projects = Project.objects.filter(tenant=tenant).select_related('ward').prefetch_related('media').order_by('-updated_at')[:6]
    pending = Project.objects.filter(tenant=tenant, verification_status=Project.Verification.SUBMITTED).select_related('ward')[:6]
    recent_media = ProjectMedia.objects.filter(project__tenant=tenant).select_related('project').order_by('-id')[:6]
    return render(request, 'impact/control/dashboard.html', _dashboard_context(
        request, projects=projects, pending=pending, recent_media=recent_media
    ))


@tenant_staff_required
def control_projects(request):
    qs = Project.objects.filter(tenant=request.tenant).select_related('ward').prefetch_related('media')
    q = request.GET.get('q','').strip()
    status = request.GET.get('status','').strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(record_id__icontains=q) | Q(project_location__icontains=q))
    if status:
        qs = qs.filter(verification_status=status)
    return render(request, 'impact/control/projects.html', _dashboard_context(request, projects=qs, q=q, status=status))


@tenant_staff_required
@transaction.atomic
def control_project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            project = form.save(commit=False)
            project.tenant = request.tenant
            if not project.record_id:
                project.record_id = _next_record_id(request.tenant, project.ward.name, project.sector)
            project.save()
            messages.success(request, f'{project.record_id} created.')
            return redirect('control-project-edit', pk=project.pk)
    else:
        form = ProjectForm(tenant=request.tenant)
    return render(request, 'impact/control/project_form.html', _dashboard_context(request, form=form, mode='create'))


@tenant_staff_required
@transaction.atomic
def control_project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project, tenant=request.tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully.')
            return redirect('control-project-edit', pk=project.pk)
    else:
        form = ProjectForm(instance=project, tenant=request.tenant)
    media_items = ProjectMedia.objects.filter(project=project).order_by('display_order','id')
    media_batch_form = ProjectMediaBatchForm()
    return render(request, 'impact/control/project_form.html', _dashboard_context(
        request, form=form, project=project, mode='edit', media_items=media_items,
        media_batch_form=media_batch_form
    ))


@tenant_staff_required
@transaction.atomic
def control_project_media_batch_upload(request, pk):
    project = get_object_or_404(Project, pk=pk, tenant=request.tenant)
    if request.method != 'POST':
        return redirect('control-project-edit', pk=project.pk)

    form = ProjectMediaBatchForm(request.POST, request.FILES)
    if not form.is_valid():
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')
        return redirect('control-project-edit', pk=project.pk)

    files = form.cleaned_data['files']
    caption = form.cleaned_data.get('caption', '').strip()
    location_label = form.cleaned_data.get('location_label', '').strip() or project.project_location
    evidence_status = form.cleaned_data['evidence_status']
    tv_enabled = form.cleaned_data.get('tv_enabled', False)
    show_location_overlay = form.cleaned_data.get('show_location_overlay', False)
    has_cover = ProjectMedia.objects.filter(project=project, is_cover=True).exists()
    last_order = ProjectMedia.objects.filter(project=project).order_by('-display_order').values_list('display_order', flat=True).first() or 0

    created = 0
    for offset, uploaded in enumerate(files, start=1):
        content_type = (getattr(uploaded, 'content_type', '') or '').lower()
        name = uploaded.name or f'asset-{offset}'
        is_video = content_type.startswith('video/') or name.lower().endswith(('.mp4','.mov','.m4v','.webm','.avi'))
        media_type = ProjectMedia.MediaType.VIDEO if is_video else ProjectMedia.MediaType.IMAGE
        asset = ProjectMedia.objects.create(
            project=project, media_type=media_type, title=name.rsplit('.', 1)[0].replace('_',' ').replace('-',' ').strip().title(),
            caption=caption, location_label=location_label, local_file=uploaded,
            tv_enabled=tv_enabled, show_location_overlay=show_location_overlay,
            display_order=last_order + offset, evidence_status=evidence_status,
            is_cover=(not has_cover and not is_video),
        )
        if asset.local_file and not asset.original_s3_key:
            asset.original_s3_key = asset.local_file.name
            asset.save(update_fields=['original_s3_key'])
        if asset.is_cover:
            has_cover = True
        created += 1

    messages.success(request, f'{created} media asset{"s" if created != 1 else ""} uploaded to this project.')
    return redirect('control-project-edit', pk=project.pk)


@tenant_staff_required
@transaction.atomic
def control_project_media_set_cover(request, pk, media_id):
    project = get_object_or_404(Project, pk=pk, tenant=request.tenant)
    media = get_object_or_404(ProjectMedia, pk=media_id, project=project)
    if request.method == 'POST' and media.media_type == ProjectMedia.MediaType.IMAGE:
        ProjectMedia.objects.filter(project=project, is_cover=True).update(is_cover=False)
        media.is_cover = True
        media.save(update_fields=['is_cover'])
        messages.success(request, 'Project cover photo updated.')
    return redirect('control-project-edit', pk=project.pk)


@tenant_staff_required
@transaction.atomic
def control_project_media_delete(request, pk, media_id):
    project = get_object_or_404(Project, pk=pk, tenant=request.tenant)
    media = get_object_or_404(ProjectMedia, pk=media_id, project=project)
    if request.method == 'POST':
        was_cover = media.is_cover
        media.delete()
        if was_cover:
            replacement = ProjectMedia.objects.filter(project=project, media_type=ProjectMedia.MediaType.IMAGE).order_by('display_order','id').first()
            if replacement:
                replacement.is_cover = True
                replacement.save(update_fields=['is_cover'])
        messages.success(request, 'Media asset removed.')
    return redirect('control-project-edit', pk=project.pk)


@tenant_staff_required
@transaction.atomic
def control_project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        title = project.short_title or project.title
        project.delete()
        messages.success(request, f'{title} deleted.')
        return redirect('control-projects')
    return render(request, 'impact/control/confirm_delete.html', _dashboard_context(request, object=project, object_type='project'))


@tenant_staff_required
def control_media(request):
    items = ProjectMedia.objects.filter(project__tenant=request.tenant).select_related('project').order_by('-id')
    return render(request, 'impact/control/media.html', _dashboard_context(request, media_items=items))


@tenant_staff_required
@transaction.atomic
def control_media_create(request):
    if request.method == 'POST':
        form = ProjectMediaForm(request.POST, request.FILES, tenant=request.tenant)
        if form.is_valid():
            media = form.save()
            if media.local_file and not media.original_s3_key:
                media.original_s3_key = media.local_file.name
                media.save(update_fields=['original_s3_key'])
            messages.success(request, 'Media asset uploaded.')
            return redirect('control-media')
    else:
        form = ProjectMediaForm(tenant=request.tenant)
    return render(request, 'impact/control/media_form.html', _dashboard_context(request, form=form))


@tenant_staff_required
@transaction.atomic
def control_bursaries(request):
    tenant = request.tenant
    summaries = BursaryWardSummary.objects.filter(tenant=tenant).select_related('ward')
    if request.method == 'POST':
        form = BursaryWardSummaryForm(request.POST, tenant=tenant)
        if form.is_valid():
            cleaned = form.cleaned_data
            defaults = {
                k: cleaned[k] for k in [
                    'students_supported','amount_allocated','secondary_count',
                    'college_tvet_count','university_count','female_count','male_count',
                    'notes','verified','tv_enabled'
                ]
            }
            row, created = BursaryWardSummary.objects.update_or_create(
                tenant=tenant,
                ward=cleaned['ward'],
                reporting_period=cleaned['reporting_period'],
                defaults=defaults,
            )
            messages.success(request, f'Bursary figures {"created" if created else "updated"} for {row.ward.name}.')
            return redirect('control-bursaries')
    else:
        form = BursaryWardSummaryForm(tenant=tenant)

    verified = summaries.filter(verified=True, tv_enabled=True)
    totals = verified.aggregate(students=Sum('students_supported'), amount=Sum('amount_allocated'))
    return render(request, 'impact/control/bursaries.html', _dashboard_context(
        request,
        summaries=summaries,
        form=form,
        bursary_students=totals['students'] or 0,
        bursary_amount=totals['amount'] or 0,
        bursary_wards=verified.values('ward_id').distinct().count(),
    ))


@tenant_staff_required
def control_evidence(request):
    items = EvidenceDocument.objects.filter(project__tenant=request.tenant).select_related('project').order_by('-uploaded_at')
    return render(request, 'impact/control/evidence.html', _dashboard_context(request, evidence_items=items))


@tenant_staff_required
@transaction.atomic
def control_evidence_create(request):
    if request.method == 'POST':
        form = EvidenceForm(request.POST, request.FILES, tenant=request.tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evidence record added.')
            return redirect('control-evidence')
    else:
        form = EvidenceForm(tenant=request.tenant)
    return render(request, 'impact/control/evidence_form.html', _dashboard_context(request, form=form))


@tenant_staff_required
def control_wards(request):
    wards = Ward.objects.filter(tenant=request.tenant)
    return render(request, 'impact/control/wards.html', _dashboard_context(request, wards=wards))


@tenant_staff_required
@transaction.atomic
def control_ward_create(request):
    if request.method == 'POST':
        form = WardForm(request.POST)
        if form.is_valid():
            ward = form.save(commit=False)
            ward.tenant = request.tenant
            ward.save()
            messages.success(request, 'Area added.')
            return redirect('control-wards')
    else:
        form = WardForm()
    return render(request, 'impact/control/ward_form.html', _dashboard_context(request, form=form))


@tenant_staff_required
@transaction.atomic
def control_tv_settings(request):
    tenant = request.tenant
    if request.method == 'POST':
        form = TenantTVSettingsForm(request.POST, request.FILES, instance=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'TV experience settings updated.')
            return redirect('control-tv-settings')
    else:
        form = TenantTVSettingsForm(instance=tenant)
    return render(request, 'impact/control/tv_settings.html', _dashboard_context(request, form=form))


@tenant_staff_required
@transaction.atomic
def control_branding(request):
    tenant = request.tenant
    if request.method == 'POST':
        form = TenantBrandForm(request.POST, instance=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Brand and language settings updated.')
            return redirect('control-branding')
    else:
        form = TenantBrandForm(instance=tenant)
    return render(request, 'impact/control/branding.html', _dashboard_context(request, form=form))


@tenant_staff_required
def control_verification(request):
    projects = Project.objects.filter(
        tenant=request.tenant, verification_status=Project.Verification.SUBMITTED
    ).select_related('ward').prefetch_related('documents', 'media')
    return render(request, 'impact/control/verification.html', _dashboard_context(request, projects=projects))


@tenant_staff_required
@transaction.atomic
def control_verify_project(request, pk):
    project = get_object_or_404(Project, pk=pk, tenant=request.tenant)
    if request.method == 'POST':
        project.verification_status = Project.Verification.VERIFIED
        project.save(update_fields=['verification_status','updated_at'])
        messages.success(request, f'{project.record_id} marked verified.')
    return redirect('control-verification')
