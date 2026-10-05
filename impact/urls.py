from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('tv/', views.tv, name='tv'),
    path('studio/post-to-tv/', views.post_to_tv_studio, name='post-to-tv-studio'),
    path('projects/<slug:slug>/', views.project_detail, name='project-detail'),
    path('api/tv-playlist/', views.tv_playlist_api, name='tv-playlist-api'),
    path('qr/', views.tenant_qr, name='tenant-qr'),

    # Premium custom control centre
    path('control/login/', views.control_login, name='control-login'),
    path('control/logout/', views.control_logout, name='control-logout'),
    path('control/', views.control_dashboard, name='control-dashboard'),
    path('control/projects/', views.control_projects, name='control-projects'),
    path('control/projects/new/', views.control_project_create, name='control-project-create'),
    path('control/projects/<int:pk>/edit/', views.control_project_edit, name='control-project-edit'),
    path('control/projects/<int:pk>/delete/', views.control_project_delete, name='control-project-delete'),
    path('control/projects/<int:pk>/media/upload/', views.control_project_media_batch_upload, name='control-project-media-batch-upload'),
    path('control/projects/<int:pk>/media/<int:media_id>/cover/', views.control_project_media_set_cover, name='control-project-media-set-cover'),
    path('control/projects/<int:pk>/media/<int:media_id>/delete/', views.control_project_media_delete, name='control-project-media-delete'),
    path('control/media/', views.control_media, name='control-media'),
    path('control/media/new/', views.control_media_create, name='control-media-create'),
    path('control/evidence/', views.control_evidence, name='control-evidence'),
    path('control/evidence/new/', views.control_evidence_create, name='control-evidence-create'),
    path('control/wards/', views.control_wards, name='control-wards'),
    path('control/wards/new/', views.control_ward_create, name='control-ward-create'),
    path('control/branding/', views.control_branding, name='control-branding'),
    path('control/tv-settings/', views.control_tv_settings, name='control-tv-settings'),
    path('control/verification/', views.control_verification, name='control-verification'),
    path('control/verification/<int:pk>/verify/', views.control_verify_project, name='control-verify-project'),
]
