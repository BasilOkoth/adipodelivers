from django import forms
from .models import Tenant, Ward, Project, ProjectMedia, EvidenceDocument, BursaryWardSummary


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
            'entry_source','story_priority','tv_enabled','published','featured',
        ]
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 5, 'placeholder':'What changed, for whom, and why it matters.'}),
            'summary_local': forms.Textarea(attrs={'rows': 4}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'completion_date': forms.DateInput(attrs={'type': 'date'}),
            'latitude': forms.NumberInput(attrs={'step':'0.000001'}),
            'longitude': forms.NumberInput(attrs={'step':'0.000001'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            self.fields['ward'].queryset = Ward.objects.filter(tenant=tenant)
        self.fields['entry_source'].help_text = 'Manual, imported from a public update, or seeded starter content.'
        self.fields['story_priority'].help_text = 'Flagship stories receive stronger placement across the experience.'


class ProjectMediaForm(StyledModelForm):
    class Meta:
        model = ProjectMedia
        fields = [
            'project','media_type','title','caption','caption_local','location_label',
            'location_label_local','latitude','longitude','local_file','duration_seconds',
            'tv_enabled','tv_start_seconds','tv_end_seconds','show_location_overlay',
            'display_order','evidence_status','is_cover',
        ]

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            self.fields['project'].queryset = Project.objects.filter(tenant=tenant)


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput(attrs={
            'multiple': True,
            'accept': 'image/*,video/*',
            'class': 'control-input media-batch-input',
        }))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_clean(d, initial) for d in data]
        return [single_clean(data, initial)] if data else []


class ProjectMediaBatchForm(forms.Form):
    files = MultipleFileField(
        label='Photos & videos',
        help_text='Select several photos and videos in one upload.',
    )
    caption = forms.CharField(required=False, max_length=300, widget=forms.Textarea(attrs={
        'rows': 3, 'class':'control-input',
        'placeholder':'Optional shared caption. You can refine each asset later.'
    }))
    location_label = forms.CharField(required=False, max_length=180, widget=forms.TextInput(attrs={
        'class':'control-input', 'placeholder':'e.g. Kogweno Primary School · Wang’chieng'
    }))
    evidence_status = forms.ChoiceField(choices=ProjectMedia.Evidence.choices, initial=ProjectMedia.Evidence.SUBMITTED,
                                        widget=forms.Select(attrs={'class':'control-input'}))
    tv_enabled = forms.BooleanField(required=False, initial=True)
    show_location_overlay = forms.BooleanField(required=False, initial=False)


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
