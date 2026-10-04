# AdipoDelivers / Karachuonyo Impact — Django edition

Django-backed constituency impact and public-accountability platform with a premium TV channel and AWS-ready video pipeline.

## What changed from the static prototype
- Real Django database models for wards, projects, impacts, media and evidence documents.
- Django Admin is the publishing control room.
- TV mode reads a live JSON playlist from `/api/tv-playlist/`.
- Every project has a **project location / route**.
- Every video has a separate **clip location** plus optional GPS coordinates.
- TV videos automatically show a premium location lower-third when `show_location_overlay=True`.
- Project records expose verification state instead of silently treating submitted claims as verified.
- AWS fields exist for original S3 key, HLS manifest, MP4 fallback and poster URL.

## Location model
Use both levels:
1. `Project.project_location` — the wider site/route, e.g. `Alara → Angang Market → ... → Kaimbo Beach`.
2. `ProjectMedia.location_label` — where the specific clip was recorded, e.g. `Nyapuodi Beach · West Karachuonyo`.
3. Optional `latitude` / `longitude` can support maps, audit trails and future GPS overlays.

This prevents a clip filmed at one junction from being misleadingly labelled as if it showed the entire project route.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

Open:
- Website: http://127.0.0.1:8000/
- TV: http://127.0.0.1:8000/tv/
- Admin: http://127.0.0.1:8000/admin/
- TV JSON: http://127.0.0.1:8000/api/tv-playlist/

## AWS production media architecture
`Admin upload → S3 originals → EventBridge/Lambda → MediaConvert → S3 outputs → CloudFront → Website + TV`

Recommended outputs:
- HLS adaptive bitrate: 1080p / 720p / 480p
- 1080p MP4 fallback
- poster/thumbnail
- optional captions
- short TV highlight window

The database is already prepared for:
- `original_s3_key`
- `hls_manifest_url`
- `mp4_fallback_url`
- `poster_url`
- `tv_start_seconds` / `tv_end_seconds`
- `location_label`
- GPS

## Production work still required for automatic transcoding
The models are AWS-ready, but automatic S3 upload + MediaConvert job submission should be implemented after the target AWS bucket, CloudFront domain, IAM MediaConvert role and output naming convention are known. Do not commit AWS keys; use environment/IAM credentials.

## Publication discipline
A record should move from `Submitted` to `Verified` only when adequate evidence is attached and attribution/funding/implementation details are accurate.

## Production storage behavior
When `AWS_STORAGE_BUCKET_NAME` is set, Django uploaded media uses S3 automatically through `django-storages`. Static assets stay on WhiteNoise. If `DATABASE_URL` is present, the project uses PostgreSQL via `dj-database-url`; otherwise it falls back to SQLite for local development.

`impact.services.submit_mediaconvert_job(media)` includes a ready MediaConvert job definition for HLS 1080/720/480 plus a 1080p MP4 fallback. Wire it to your preferred trigger after the AWS IAM role, bucket and output lifecycle are finalized.

## Post-to-TV Studio

Staff users can open `/studio/post-to-tv/` to convert a Facebook/social update into a TV-ready project story.

Workflow:
1. Paste the original post and optionally its source URL.
2. Click **Analyse Post**.
3. The parser proposes ward, sector, title, intervention, route/location, summary and expected impacts.
4. Campaign/slogan-like lines are separated from the factual project record.
5. Staff review and edit every field.
6. Optionally upload a video and give the clip its exact filming location.
7. Save as draft or publish to both the website and TV playlist.

Every imported record defaults to **Submitted · verification pending**. The Studio never upgrades a claim to Verified automatically. The original source text and parsed result are retained in `SourcePost` for auditability.

The parser is deliberately deterministic and local in this build, so the feature works without an external AI API. A future LLM extraction provider can be added behind the same review workflow without changing the publishing model.

# Multi-tenant product architecture

The project is now **multi-tenant from the shared core**. `AdipoDelivers` is one tenant, not a separate codebase.

## Isolation model
This build uses **row-level multi-tenancy** in one PostgreSQL database. Every public content record belongs to a `Tenant`; project uniqueness is scoped per tenant, and `Ward`/area names are scoped per tenant. This is simpler to operate than cloning deployments and works well for a SaaS-style product on Render/AWS.

Core tenant models:
- `Tenant` — brand, leader/office, jurisdiction, colors, public domain, local area terminology and profile metadata.
- `TenantDomain` — maps custom hostnames to tenants (`adipodelivers.org`, another client's domain, etc.).
- `TenantMembership` — assigns users to a tenant with Owner/Admin/Editor/Viewer roles.
- `Ward` — internally named Ward for compatibility, but tenant UI can label these units as wards, sub-counties, locations, zones, etc.
- `Project`, `SourcePost`, media and evidence — tenant-isolated through the project/source ownership chain.

`TenantResolutionMiddleware` resolves `request.tenant` from the incoming hostname before public views run. In local DEBUG mode you can switch the active tenant with `?tenant=<slug>`; the selection is stored in the local session.

## One codebase, many branded deployments
Examples:

```text
adipodelivers.org        → Tenant: adipodelivers
anothermpimpact.org      → Tenant: another-mp
countyresults.example    → Tenant: county-results
```

Each can have its own:
- public domain
- platform name / brand mark / colors / logo
- leader and office title
- constituency/county/jurisdiction name
- wards or other geographic units
- projects, evidence, photos and videos
- Post-to-TV Studio source posts
- TV playlist and location overlays
- automatically generated tenant QR code
- staff/owner accounts

The TV JSON API is tenant-aware, so `/api/tv-playlist/` returns only the projects for the domain being viewed. `/qr/` generates a QR code for the current tenant's public domain.

## Create a new tenant
Create the user's Django account first if the client needs an owner login, then run:

```bash
python manage.py create_tenant "Example Impact" \
  --slug example-impact \
  --domain exampleimpact.org \
  --leader "Hon. Example Leader" \
  --title "Member of Parliament" \
  --jurisdiction "Example Constituency" \
  --county "Example County" \
  --areas "Ward One,Ward Two,Ward Three" \
  --area-unit ward \
  --owner-username example_owner
```

Point the client's DNS/custom domain to the application and include the hostname in `DJANGO_ALLOWED_HOSTS`. No code clone is required.

## Local multi-tenant testing
After migrations and `seed_demo`:

```text
http://127.0.0.1:8000/?tenant=adipodelivers
http://127.0.0.1:8000/tv/?tenant=adipodelivers
```

Create additional tenants with `create_tenant`, then switch using their slug in DEBUG mode.

## Tenant security
Public queries explicitly filter on `request.tenant`. The Post-to-TV Studio also requires an active membership with Owner/Admin/Editor role (or a Django superuser). Admin querysets for tenant content are scoped to the active tenant for non-superusers.

For a larger commercial rollout, the next security hardening step should be automated tests that assert cross-tenant isolation for every read/write endpoint and admin action. Row-level PostgreSQL policies can also be added later as an additional defense-in-depth layer.

## Why row-level multi-tenancy here
A schema-per-tenant design is useful for some regulated systems, but this product benefits from a shared schema because onboarding is fast, migrations run once, AWS media infrastructure is shared, and global platform administration/analytics remain possible. Tenant-owned S3 prefixes should be used in production (for example `tenants/<tenant-slug>/originals/...`) so media organization mirrors database isolation.

## Community-language / Dholuo layer

The platform now supports a tenant-specific community language in addition to English. `AdipoDelivers` is configured for **English + Dholuo** (`luo`) and defaults to bilingual TV mode.

### Language modes

- Website: `?lang=en` or `?lang=local`
- TV: `?lang=en`, `?lang=local`, or `?lang=bilingual`
- On the TV screen, press **L** to cycle English → community language → bilingual.
- If a Dholuo/local field is blank, the system falls back to English rather than showing empty content.

### Bilingual content fields

Projects now support English plus community-language versions of:

- title / short title
- intervention
- summary
- project location / route
- impact statements
- photo/video captions
- exact media location
- ward/area display name

The **Post-to-TV Studio** exposes these fields after the English structured story is generated. The parser does not silently invent Dholuo translations; staff should enter or review local-language copy before publication. This keeps public communication accurate while still allowing premium bilingual TV presentation.

### Multi-tenant language configuration

Each tenant can choose its own second language. Example:

```bash
python manage.py create_tenant "Example Impact" \
  --domain example.org \
  --secondary-language "Dholuo" \
  --secondary-language-code luo \
  --secondary-language-short DHO \
  --bilingual-tv
```

This means another tenant can use Kiswahili or another community language without changing the codebase.

## Premium custom Control Centre
The product now has a separate tenant-aware management workspace and does not depend on Django Admin for daily operation.

- `/control/login/` — staff sign-in
- `/control/` — Impact Command Centre
- `/control/projects/` — project records
- `/studio/post-to-tv/` — Post-to-TV Studio
- `/control/media/` — photo/video library
- `/control/evidence/` — evidence library
- `/control/verification/` — verification queue
- `/control/wards/` — geography
- `/control/branding/` — tenant branding and language

Django Admin may remain available to a platform superuser as an emergency/backend utility, but tenant staff should use the Control Centre.

Uploaded media now uses tenant-aware S3 paths such as `tenants/<tenant>/originals/<record>/...`, and evidence uses `tenants/<tenant>/evidence/<record>/...`.

### Render deployment note
The Blueprint keeps AWS credentials out of GitHub. Render prompts only for `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`. The S3 bucket, Stockholm region and MediaConvert role are already declared. CloudFront remains optional until a distribution is configured.
