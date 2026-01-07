"""
Firebase Authentication for Django REST Framework
"""

from rest_framework import authentication, exceptions
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from backend.firebase_utils import verify_firebase_token, get_or_create_user_from_firebase


class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    Firebase Authentication backend for Django REST Framework
    """

    def authenticate(self, request):
        """
        Authenticate user based on Firebase ID token in Authorization header
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header:
            return None

        # Check if it's a Firebase token (Bearer token)
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        # Verify Firebase token
        firebase_user = verify_firebase_token(token)

        if not firebase_user:
            raise exceptions.AuthenticationFailed(_('Invalid Firebase token'))

        # Get or create Django user
        user = get_or_create_user_from_firebase(firebase_user)

        return (user, None)


class FirebaseTokenAuthentication(authentication.BaseAuthentication):
    """
    Alternative Firebase authentication that accepts token in query parameter
    Useful for development and testing
    """

    def authenticate(self, request):
        """
        Authenticate user based on Firebase ID token in query parameter
        """
        token = request.GET.get('firebase_token') or request.POST.get('firebase_token')

        if not token:
            return None

        # Verify Firebase token
        firebase_user = verify_firebase_token(token)

        if not firebase_user:
            raise exceptions.AuthenticationFailed(_('Invalid Firebase token'))

        # Get or create Django user
        user = get_or_create_user_from_firebase(firebase_user)

        return (user, None)