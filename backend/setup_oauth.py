import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_backend.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

site, _ = Site.objects.get_or_create(id=1, defaults={'domain': 'localhost', 'name': 'localhost'})

google_app, _ = SocialApp.objects.get_or_create(
    provider='google',
    defaults={
        'name': 'Google',
        'client_id': 'YOUR_GOOGLE_CLIENT_ID',
        'secret': 'YOUR_GOOGLE_SECRET',
    }
)
google_app.sites.add(site)

github_app, _ = SocialApp.objects.get_or_create(
    provider='github',
    defaults={
        'name': 'GitHub',
        'client_id': 'YOUR_GITHUB_CLIENT_ID',
        'secret': 'YOUR_GITHUB_SECRET',
    }
)
github_app.sites.add(site)

print("OAuth setup complete.")
