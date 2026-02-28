from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # OAuth (allauth)
    path('api/auth/oauth/', include('allauth.urls')),

    # App URLs
    path('api/auth/',  include('users.urls')),
    path('api/',       include('blog.urls')),
    path('api/',       include('comments.urls')),
    path('api/',       include('reactions.urls')),
    path('api/',       include('mediafiles.urls')),
    path('api/',       include('notifications.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)