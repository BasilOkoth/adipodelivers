#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path.cwd()
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = ROOT / ".bursary-feature-backup" / STAMP
TV_FUNCTIONS = '\nfunction bursaryMoney(v){\n  const n=Number(v||0);\n  if(!Number.isFinite(n)||n<=0)return \'—\';\n  if(n>=1000000)return `KES ${(n/1000000).toFixed(n>=10000000?1:2).replace(/\\.0+$/,\'\')}M`;\n  if(n>=1000)return `KES ${(n/1000).toFixed(0)}K`;\n  return `KES ${n.toLocaleString(\'en-KE\')}`;\n}\n\nfunction bursaryOverviewSlide(data,b){\n  const x=data.bursary||{};\n  const periods=(x.periods||[]).join(\' · \');\n  return {\n    duration:11000,\n    ticker:ticker([\n      `${Number(x.students||0).toLocaleString(\'en-KE\')} students supported`,\n      `${x.wards_reached||0} wards`,\n      Number(x.amount||0)>0?`${bursaryMoney(x.amount)} verified bursary allocation`:\'\',\n      periods?`Reporting period: ${periods}`:\'\',\n      b.domain?`Explore: ${b.domain}`:\'\'\n    ]),\n    html:`<section class="slide bursary-overview">\n      <div class="bursary-overview-copy">\n        <div class="bursary-kicker">EDUCATION SUPPORT · BURSARY IMPACT</div>\n        <h2>Investing in<br><span>Karachuonyo\'s future.</span></h2>\n        <p>Verified ward-level education support shown as aggregate public-impact figures.</p>\n        <div class="bursary-period">${esc(periods||\'Current verified reporting period\')}</div>\n      </div>\n      <div class="bursary-hero-metrics">\n        <div class="bursary-big-card primary"><small>STUDENTS SUPPORTED</small><strong>${Number(x.students||0).toLocaleString(\'en-KE\')}</strong><span>Across verified ward records</span></div>\n        <div class="bursary-big-card"><small>VERIFIED ALLOCATION</small><strong>${esc(bursaryMoney(x.amount))}</strong><span>Education bursary support</span></div>\n        <div class="bursary-mini-grid">\n          <div><strong>${x.wards_reached||0}</strong><span>Wards reached</span></div>\n          <div><strong>${Number(x.secondary||0).toLocaleString(\'en-KE\')}</strong><span>Secondary</span></div>\n          <div><strong>${Number(x.college_tvet||0).toLocaleString(\'en-KE\')}</strong><span>College / TVET</span></div>\n          <div><strong>${Number(x.university||0).toLocaleString(\'en-KE\')}</strong><span>University</span></div>\n        </div>\n      </div>\n    </section>`\n  };\n}\n\nfunction bursaryWardSlide(data,b){\n  const x=data.bursary||{}, rows=x.wards||[];\n  const max=Math.max(1,...rows.map(r=>Number(r.students||0)));\n  const bars=rows.map((r,idx)=>{\n    const width=Math.max(3,Math.round((Number(r.students||0)/max)*100));\n    return `<div class="ward-bursary-row">\n      <div class="ward-bursary-rank">${String(idx+1).padStart(2,\'0\')}</div>\n      <div class="ward-bursary-name"><b>${esc(r.ward)}</b><span>${esc(r.period||\'\')}</span></div>\n      <div class="ward-bursary-bar"><i style="width:${width}%"></i></div>\n      <div class="ward-bursary-count"><strong>${Number(r.students||0).toLocaleString(\'en-KE\')}</strong><span>students</span></div>\n      <div class="ward-bursary-money">${Number(r.amount||0)>0?esc(bursaryMoney(r.amount)):\'—\'}</div>\n    </div>`;\n  }).join(\'\');\n  return {\n    duration:12000,\n    ticker:ticker(rows.map(r=>`${r.ward}: ${Number(r.students||0).toLocaleString(\'en-KE\')} students`).concat([b.domain?`More: ${b.domain}`:\'\'])),\n    html:`<section class="slide bursary-wards">\n      <div class="bursary-ward-head">\n        <div><div class="bursary-kicker">WARD-BY-WARD BURSARY REACH</div><h2>Education support across the constituency.</h2></div>\n        <div class="bursary-total-chip"><strong>${Number(x.students||0).toLocaleString(\'en-KE\')}</strong><span>Total students</span></div>\n      </div>\n      <div class="ward-bursary-list">${bars}</div>\n      <div class="bursary-footnote">Verified aggregate figures only · No individual student records displayed</div>\n    </section>`\n  };\n}\n'
TV_CSS = '\n/* BURSARY IMPACT TV */\n.bursary-overview{\n  padding:34px 42px;\n  display:grid;grid-template-columns:minmax(0,.9fr) minmax(520px,1.1fr);gap:34px;align-items:center;\n  background:\n    radial-gradient(circle at 78% 16%,rgba(230,189,102,.10),transparent 24%),\n    radial-gradient(circle at 18% 80%,rgba(214,31,38,.12),transparent 30%),\n    linear-gradient(145deg,#080b10,#050608);\n}\n.bursary-kicker{color:var(--gold);font:900 12px Inter;letter-spacing:.17em;text-transform:uppercase}\n.bursary-overview h2{margin:14px 0 18px;font:900 clamp(58px,5vw,94px)/.92 Manrope;letter-spacing:-.06em}\n.bursary-overview h2 span{color:var(--gold)}\n.bursary-overview p{max-width:690px;color:#c7d0d8;font-size:clamp(20px,1.25vw,25px);line-height:1.45}\n.bursary-period{display:inline-flex;margin-top:22px;padding:9px 12px;border-radius:8px;background:rgba(255,255,255,.055);border:1px solid var(--line);font:800 11px Inter;letter-spacing:.1em}\n.bursary-hero-metrics{display:grid;grid-template-columns:1fr 1fr;gap:12px}\n.bursary-big-card{min-height:230px;padding:24px;border-radius:22px;background:linear-gradient(155deg,#131922,#0b0f14);border:1px solid var(--line);display:flex;flex-direction:column;justify-content:flex-end}\n.bursary-big-card.primary{background:linear-gradient(155deg,#481016,#1b0b0e);border-color:rgba(214,31,38,.38)}\n.bursary-big-card small{font:900 10px Inter;letter-spacing:.14em;color:#a9b3bd}\n.bursary-big-card strong{margin-top:10px;font:900 clamp(43px,3.4vw,68px)/.95 Manrope;color:#fff}\n.bursary-big-card span{margin-top:10px;color:#9eabb6;font-size:13px}\n.bursary-mini-grid{grid-column:1/-1;display:grid;grid-template-columns:repeat(4,1fr);gap:10px}\n.bursary-mini-grid>div{padding:16px;border-radius:15px;background:#0d1218;border:1px solid var(--line)}\n.bursary-mini-grid strong,.bursary-mini-grid span{display:block}\n.bursary-mini-grid strong{font:900 25px Manrope;color:var(--gold)}\n.bursary-mini-grid span{margin-top:5px;color:#9da8b3;font-size:11px}\n\n.bursary-wards{padding:28px 34px;display:grid;grid-template-rows:auto minmax(0,1fr) auto;gap:18px;background:linear-gradient(145deg,#080b10,#050608)}\n.bursary-ward-head{display:flex;justify-content:space-between;align-items:end;gap:22px}\n.bursary-ward-head h2{margin:9px 0 0;font:900 clamp(43px,3.6vw,70px)/.95 Manrope;letter-spacing:-.05em}\n.bursary-total-chip{min-width:160px;padding:13px 16px;border-radius:14px;background:#10161d;border:1px solid var(--line);text-align:right}\n.bursary-total-chip strong,.bursary-total-chip span{display:block}.bursary-total-chip strong{font:900 28px Manrope;color:var(--gold)}.bursary-total-chip span{font-size:10px;color:#9fa9b3;text-transform:uppercase;letter-spacing:.1em}\n.ward-bursary-list{display:grid;gap:8px;align-content:center}\n.ward-bursary-row{display:grid;grid-template-columns:44px minmax(150px,.9fr) minmax(260px,2fr) 120px 130px;gap:14px;align-items:center;padding:11px 13px;border-radius:13px;background:#0d1218;border:1px solid rgba(255,255,255,.075)}\n.ward-bursary-rank{font:900 14px Manrope;color:#65717d}\n.ward-bursary-name b,.ward-bursary-name span{display:block}.ward-bursary-name b{font:800 16px Manrope}.ward-bursary-name span{margin-top:3px;color:#7f8a95;font-size:10px}\n.ward-bursary-bar{height:10px;border-radius:99px;background:#202832;overflow:hidden}.ward-bursary-bar i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--accent),#efbd61)}\n.ward-bursary-count{text-align:right}.ward-bursary-count strong,.ward-bursary-count span{display:block}.ward-bursary-count strong{font:900 19px Manrope}.ward-bursary-count span{font-size:9px;color:#8e99a4;text-transform:uppercase}\n.ward-bursary-money{text-align:right;font:800 13px Manrope;color:var(--gold)}\n.bursary-footnote{text-align:right;color:#6f7b86;font:700 10px Inter;letter-spacing:.08em;text-transform:uppercase}\n@media(max-width:1280px){\n  .bursary-overview{padding:24px 28px;grid-template-columns:minmax(0,.9fr) minmax(440px,1.1fr)}\n  .bursary-big-card{min-height:190px;padding:18px}\n  .ward-bursary-row{grid-template-columns:36px minmax(130px,.8fr) minmax(200px,1.6fr) 100px 110px;gap:10px;padding:9px 11px}\n}\n'

FILES = [
    "impact/models.py","impact/forms.py","impact/views.py","impact/urls.py","impact/admin.py",
    "templates/impact/control/base.html","static/impact/js/tv-django.js","static/impact/css/tv.css"
]

def fail(msg):
    raise SystemExit("INSTALL STOPPED: " + msg)

def backup():
    for rel in FILES:
        p=ROOT/rel
        if not p.exists(): fail(f"Missing required file: {rel}")
        dst=BACKUP/rel
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,dst)

def append_once(path, marker, content):
    p=ROOT/path
    s=p.read_text(encoding="utf-8")
    if marker in s: return
    p.write_text(s.rstrip()+"\n\n"+content.strip()+"\n",encoding="utf-8")

def replace_once(path, old, new, label):
    p=ROOT/path
    s=p.read_text(encoding="utf-8")
    if new in s: return
    if old not in s:
        fail(f"Could not find patch point for {label} in {path}. Your repo may have changed.")
    p.write_text(s.replace(old,new,1),encoding="utf-8")

def main():
    if not (ROOT/"manage.py").exists():
        fail("Run this script from the adipodelivers repository root.")
    backup()

    append_once("impact/models.py","class BursaryWardSummary(models.Model):", '''
class BursaryWardSummary(models.Model):
    """Verified aggregate bursary support by ward. Never stores individual student records."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='bursary_summaries')
    ward = models.ForeignKey(Ward, on_delete=models.PROTECT, related_name='bursary_summaries')
    reporting_period = models.CharField(max_length=40, default='2026')
    students_supported = models.PositiveIntegerField(default=0)
    amount_allocated = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    secondary_count = models.PositiveIntegerField(default=0)
    college_tvet_count = models.PositiveIntegerField(default=0)
    university_count = models.PositiveIntegerField(default=0)
    female_count = models.PositiveIntegerField(default=0)
    male_count = models.PositiveIntegerField(default=0)
    notes = models.CharField(max_length=240, blank=True)
    verified = models.BooleanField(default=False)
    tv_enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ward__display_order', 'ward__name']
        unique_together = [('tenant', 'ward', 'reporting_period')]

    def __str__(self):
        return f'{self.ward.name} · {self.reporting_period} · {self.students_supported} students'
''')

    replace_once("impact/forms.py",
        "from .models import Tenant, Ward, Project, ProjectMedia, EvidenceDocument",
        "from .models import Tenant, Ward, Project, ProjectMedia, EvidenceDocument, BursaryWardSummary",
        "forms model import")

    append_once("impact/forms.py","class BursaryWardSummaryForm(StyledModelForm):", '''
class BursaryWardSummaryForm(StyledModelForm):
    class Meta:
        model = BursaryWardSummary
        fields = [
            'ward','reporting_period','students_supported','amount_allocated',
            'secondary_count','college_tvet_count','university_count',
            'female_count','male_count','notes','verified','tv_enabled',
        ]
        widgets = {
            'amount_allocated': forms.NumberInput(attrs={'step':'0.01','min':'0'}),
            'students_supported': forms.NumberInput(attrs={'min':'0'}),
            'secondary_count': forms.NumberInput(attrs={'min':'0'}),
            'college_tvet_count': forms.NumberInput(attrs={'min':'0'}),
            'university_count': forms.NumberInput(attrs={'min':'0'}),
            'female_count': forms.NumberInput(attrs={'min':'0'}),
            'male_count': forms.NumberInput(attrs={'min':'0'}),
            'notes': forms.TextInput(attrs={'placeholder':'Optional factual note'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            self.fields['ward'].queryset = Ward.objects.filter(tenant=tenant)

    def clean(self):
        cleaned = super().clean()
        total = cleaned.get('students_supported') or 0
        education = sum(cleaned.get(k) or 0 for k in ('secondary_count','college_tvet_count','university_count'))
        gender = (cleaned.get('female_count') or 0) + (cleaned.get('male_count') or 0)
        if education and education > total:
            raise forms.ValidationError('Secondary + College/TVET + University cannot exceed total students supported.')
        if gender and gender > total:
            raise forms.ValidationError('Female + Male counts cannot exceed total students supported.')
        return cleaned
''')

    replace_once("impact/views.py","from django.db.models import Q","from django.db.models import Q, Sum","Sum import")
    replace_once("impact/views.py",
        "from .models import Project, Ward, ProjectImpact, ProjectMedia, EvidenceDocument, SourcePost, TenantMembership",
        "from .models import Project, Ward, ProjectImpact, ProjectMedia, EvidenceDocument, SourcePost, TenantMembership, BursaryWardSummary",
        "views model import")
    replace_once("impact/views.py",
        "from .forms import ProjectForm, ProjectMediaForm, ProjectMediaBatchForm, EvidenceForm, WardForm, TenantBrandForm, TenantTVSettingsForm",
        "from .forms import ProjectForm, ProjectMediaForm, ProjectMediaBatchForm, EvidenceForm, WardForm, TenantBrandForm, TenantTVSettingsForm, BursaryWardSummaryForm",
        "views form import")

    old_api = '''    return JsonResponse({
        'tenant': tenant.slug, 'brand': brand, 'language': language,
        'wards': [{'en': w.name, 'local': w.name_local} for w in Ward.objects.filter(tenant=tenant)],
        'projects': items,
    })'''
    new_api = '''    bursary_qs = BursaryWardSummary.objects.filter(
        tenant=tenant, verified=True, tv_enabled=True
    ).select_related('ward').order_by('ward__display_order', 'ward__name')

    bursary_totals = bursary_qs.aggregate(
        students=Sum('students_supported'),
        amount=Sum('amount_allocated'),
        secondary=Sum('secondary_count'),
        college_tvet=Sum('college_tvet_count'),
        university=Sum('university_count'),
        female=Sum('female_count'),
        male=Sum('male_count'),
    )
    bursary_data = {
        'students': bursary_totals['students'] or 0,
        'amount': str(bursary_totals['amount'] or 0),
        'secondary': bursary_totals['secondary'] or 0,
        'college_tvet': bursary_totals['college_tvet'] or 0,
        'university': bursary_totals['university'] or 0,
        'female': bursary_totals['female'] or 0,
        'male': bursary_totals['male'] or 0,
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
    })'''
    replace_once("impact/views.py",old_api,new_api,"TV bursary payload")

    append_once("impact/views.py","def control_bursaries(request):", '''
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
''')

    replace_once("impact/urls.py",
        "    path('control/media/', views.control_media, name='control-media'),",
        "    path('control/media/', views.control_media, name='control-media'),\n    path('control/bursaries/', views.control_bursaries, name='control-bursaries'),",
        "bursary url")

    replace_once("templates/impact/control/base.html",
        '''      <a href="{% url 'control-media' %}"><span class="ico">◫</span><span>Field Media</span></a>''',
        '''      <a href="{% url 'control-media' %}"><span class="ico">◫</span><span>Field Media</span></a>
      <a href="{% url 'control-bursaries' %}"><span class="ico">🎓</span><span>Bursary Impact</span></a>''',
        "control navigation")

    replace_once("impact/admin.py",
        "    ProjectMedia, EvidenceDocument, SourcePost\n)",
        "    ProjectMedia, EvidenceDocument, SourcePost, BursaryWardSummary\n)",
        "admin import")

    append_once("impact/admin.py","class BursaryWardSummaryAdmin", '''
@admin.register(BursaryWardSummary)
class BursaryWardSummaryAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ('ward','reporting_period','students_supported','amount_allocated','verified','tv_enabled')
    list_filter = ('reporting_period','verified','tv_enabled','ward')
    search_fields = ('ward__name','reporting_period','notes')
''')

    replace_once("static/impact/js/tv-django.js",
        "function build(data){",
        TV_FUNCTIONS+"\n\nfunction build(data){",
        "bursary TV functions")

    project_marker = "  projects.forEach((p,projectIndex)=>{"
    if project_marker not in (ROOT/"static/impact/js/tv-django.js").read_text(encoding="utf-8"):
        project_marker = "  projects.forEach(p=>{"
    replace_once("static/impact/js/tv-django.js",
        project_marker,
        '''  if(data.bursary?.wards?.length){
    slides.push(bursaryOverviewSlide(data,b));
    slides.push(bursaryWardSlide(data,b));
  }

'''+project_marker,
        "bursary slide insertion")

    append_once("static/impact/css/tv.css","/* BURSARY IMPACT TV */",TV_CSS)

    print("Bursary impact feature installed.")
    print("Backups:", BACKUP)
    print("Next:")
    print("  python manage.py migrate")
    print("  python manage.py check")
    print("Then open /control/bursaries/ and enter VERIFIED ward-level totals.")

if __name__ == "__main__":
    main()
