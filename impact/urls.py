from django.urls import path
from . import views
urlpatterns=[
 path('',views.home,name='home'),
 path('tv/',views.tv,name='tv'),
 path('studio/post-to-tv/',views.post_to_tv_studio,name='post-to-tv-studio'),
 path('projects/<slug:slug>/',views.project_detail,name='project-detail'),
 path('api/tv-playlist/',views.tv_playlist_api,name='tv-playlist-api'),
 path('qr/',views.tenant_qr,name='tenant-qr'),
]
