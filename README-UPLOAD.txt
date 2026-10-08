ADIPO DELIVERS — COMPLETE BURSARY FEATURE FILES

This package contains complete replacement files for the current repository integration.

UPLOAD/REPLACE:
impact/models.py
impact/forms.py
impact/views.py
impact/urls.py
impact/admin.py
impact/migrations/0008_bursary_impact.py
templates/impact/control/base.html
templates/impact/control/bursaries.html
static/impact/js/tv-django.js
static/impact/css/tv.css

IMPORTANT AFTER UPLOAD:
1. Render must deploy the new commit.
2. Run migration:
   python manage.py migrate
3. If Render's render.yaml already runs `python manage.py migrate` during pre-deploy, the migration will run automatically.
4. Then sign in and open:
   /control/bursaries/

The TV bursary slides appear ONLY when at least one bursary ward row is:
- Verified = checked
- Show on TV = checked

No student names or individual student records are stored by this feature.
