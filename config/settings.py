from pathlib import Path
import os
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY','dev-only-change-me')
DEBUG = os.getenv('DJANGO_DEBUG','1') == '1'
ALLOWED_HOSTS = [h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS','localhost,127.0.0.1').split(',') if h.strip()]
CSRF_TRUSTED_ORIGINS = [u.strip() for u in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS','').split(',') if u.strip()]
INSTALLED_APPS = ['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','impact']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware','whitenoise.middleware.WhiteNoiseMiddleware','django.contrib.sessions.middleware.SessionMiddleware','impact.middleware.TenantResolutionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF='config.urls'
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION='config.wsgi.application'

if os.getenv('DATABASE_URL'):
    import dj_database_url
    DATABASES={'default': dj_database_url.config(conn_max_age=600, ssl_require=not DEBUG)}
else:
    DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':BASE_DIR/'db.sqlite3'}}
AUTH_PASSWORD_VALIDATORS=[]
LANGUAGE_CODE='en-us'; TIME_ZONE='Africa/Nairobi'; USE_I18N=True; USE_TZ=True
STATIC_URL='/static/'; STATICFILES_DIRS=[BASE_DIR/'static']; STATIC_ROOT=BASE_DIR/'staticfiles'
MEDIA_URL='/media/'; MEDIA_ROOT=BASE_DIR/'uploads'
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'

# AWS-ready media settings. The app works locally without these.
AWS_STORAGE_BUCKET_NAME=os.getenv('AWS_STORAGE_BUCKET_NAME','')
AWS_S3_REGION_NAME=os.getenv('AWS_S3_REGION_NAME','af-south-1')
AWS_CLOUDFRONT_DOMAIN=os.getenv('AWS_CLOUDFRONT_DOMAIN','')
AWS_MEDIACONVERT_ROLE_ARN=os.getenv('AWS_MEDIACONVERT_ROLE_ARN','')
AWS_MEDIACONVERT_QUEUE_ARN=os.getenv('AWS_MEDIACONVERT_QUEUE_ARN','')

# Use S3 for uploaded media when a bucket is configured.
if AWS_STORAGE_BUCKET_NAME:
    AWS_S3_CUSTOM_DOMAIN = AWS_CLOUDFRONT_DOMAIN or f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    STORAGES = {
        'default': {'BACKEND':'storages.backends.s3.S3Storage','OPTIONS':{'bucket_name':AWS_STORAGE_BUCKET_NAME,'location':'originals'}},
        'staticfiles': {'BACKEND':'whitenoise.storage.CompressedManifestStaticFilesStorage'},
    }
else:
    STORAGES = {
        'default': {'BACKEND':'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND':'whitenoise.storage.CompressedManifestStaticFilesStorage'},
    }
