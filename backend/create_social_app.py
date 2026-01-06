import os
import django
from django.conf import settings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

# Get Google credentials from environment or use placeholders
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', 'your-google-client-id-here')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', 'your-google-client-secret-here')

# Check if we have actual credentials (not placeholders)
has_real_credentials = (
    GOOGLE_CLIENT_ID != 'your-google-client-id-here' and 
    GOOGLE_CLIENT_SECRET != 'your-google-client-secret-here' and
    GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
)

if not has_real_credentials:
    print("WARNING: Using placeholder Google OAuth credentials.")
    print("Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables with your actual Google OAuth credentials.")
    print("")
    print("To get Google OAuth credentials:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create/select a project")
    print("3. Enable Google+ API")
    print("4. Create OAuth 2.0 credentials")
    print("5. Add http://localhost:8000/accounts/google/login/callback/ as authorized redirect URI")
    print("")
    print("Your Client ID should look like: 123456789-abcdef.apps.googleusercontent.com")
    print("Your Client Secret should look like: GOCSPX-...")
else:
    print("Using credentials from environment variables.")

# Get or create the site
site, created = Site.objects.get_or_create(
    id=settings.SITE_ID,
    defaults={'domain': 'localhost:8000', 'name': 'Swad of Tamil Local'}
)

# Create or update the Google SocialApp
social_app, created = SocialApp.objects.get_or_create(
    provider='google',
    defaults={
        'name': 'Google',
        'client_id': GOOGLE_CLIENT_ID,
        'secret': GOOGLE_CLIENT_SECRET,
    }
)

# Update the credentials if they have changed
if social_app.client_id != GOOGLE_CLIENT_ID:
    social_app.client_id = GOOGLE_CLIENT_ID
    social_app.save()
if social_app.secret != GOOGLE_CLIENT_SECRET:
    social_app.secret = GOOGLE_CLIENT_SECRET
    social_app.save()

# Add the site to the social app
social_app.sites.add(site)
social_app.save()

print(f"{'CREATED' if created else 'UPDATED'} Google SocialApp")
print(f"Client ID: {social_app.client_id}")
print(f"Sites: {[s.domain for s in social_app.sites.all()]}")