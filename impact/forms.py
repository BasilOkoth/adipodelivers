from django import forms
from .models import Tenant, Ward, Project, ProjectMedia, EvidenceDocument


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            cls = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (cls + ' control-input').strip()


class ProjectForm(StyledModelForm):
    class Meta:
        model = Project
        fields = [
            'title','title_local','short_title','short_title_local','ward','sector',
            'intervention','intervention_local','summary','summary_local',
            'project_location','project_location_local','latitude','longitude',
            'start_date','completion_date','budget','funding_source','implementing_agency',
            'beneficiaries','verification_status','source_label','source_url',
            'tv_enabled','published','featured',
        ]
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 5}),
            'summary_local': forms.Textarea(attrs={'rows': 4}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'completion_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            self.fields['ward'].queryset = Ward.objects.filter(tenant=tenant)


class ProjectMediaForm(StyledModelForm):
    class Meta:
        model = ProjectMedia
        fields = [
            'project','media_type','title','caption','caption_local','location_label',
            'location_label_local','latitude','longitude','local_file','duration_seconds',
            'tv_enabled','tv_start_seconds','tv_end_seconds','show_location_overlay',
            'display_order','evidence_status',
        ]

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            self.fields['project'].queryset = Project.objects.filter(tenant=tenant)


class EvidenceForm(StyledModelForm):
    class Meta:
        model = EvidenceDocument
        fields = ['project','title','file','external_url','source_organization','verified']

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            self.fields['project'].queryset = Project.objects.filter(tenant=tenant)


class WardForm(StyledModelForm):
    class Meta:
        model = Ward
        fields = ['name','name_local','display_order']


class TenantBrandForm(StyledModelForm):
    class Meta:
        model = Tenant
        fields = [
            'public_name','leader_name','leader_title','jurisdiction_name','county_name',
            'tagline','public_domain','brand_mark','primary_color','accent_color',
            'primary_language_name','secondary_language_name','secondary_language_short',
            'bilingual_tv_enabled','default_tv_language_mode',
        ]


class TenantTVSettingsForm(StyledModelForm):
    class Meta:
        model = Tenant
        fields = [
            'leader_photo','logo','brand_mark','primary_color','accent_color',
            'tv_intro_kicker','tv_intro_headline','tv_intro_subheadline','tv_ticker_text',
            'tv_show_leader_photo','tv_show_qr','tv_show_clock','tv_show_ticker',
            'tv_show_website','tv_show_project_status','tv_intro_duration_seconds',
            'bilingual_tv_enabled','default_tv_language_mode',
        ]
        widgets = {
            'tv_intro_subheadline': forms.Textarea(attrs={'rows': 3}),
            'tv_ticker_text': forms.Textarea(attrs={'rows': 3}),
            'primary_color': forms.TextInput(attrs={'type': 'color'}),
            'accent_color': forms.TextInput(attrs={'type': 'color'}),
        }
