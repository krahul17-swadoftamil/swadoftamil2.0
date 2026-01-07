"""
Firebase Admin SDK utilities for Swad of Tamil backend
"""

import firebase_admin
from firebase_admin import auth, credentials
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)


def initialize_firebase():
    """
    Initialize Firebase Admin SDK with proper error handling
    """
    if firebase_admin._apps:
        logger.info("Firebase Admin SDK already initialized")
        return True

    # Validate Firebase config exists
    if not hasattr(settings, 'FIREBASE_CONFIG') or not settings.FIREBASE_CONFIG:
        logger.warning("Firebase config not found in settings - Firebase features will be disabled")
        return False

    required_fields = ['project_id', 'private_key', 'client_email']
    missing_fields = [field for field in required_fields if not settings.FIREBASE_CONFIG.get(field)]

    if missing_fields:
        logger.warning(f"Missing Firebase config fields: {missing_fields} - Firebase features will be disabled")
        return False

    try:
        cred = credentials.Certificate(settings.FIREBASE_CONFIG)
        firebase_admin.initialize_app(cred)
        logger.info("✅ Firebase Admin SDK initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase Admin SDK: {e}")
        logger.warning("Firebase features will be disabled - JWT authentication will still work")
        # Don't raise exception in any case to avoid breaking the server
        return False


def verify_firebase_token(id_token):
    """
    Verify Firebase ID token and return decoded token
    """
    if not id_token:
        logger.warning("Empty Firebase token provided")
        return None

    # For testing: if Firebase not initialized, return mock token
    if not firebase_admin._apps:
        logger.warning("Firebase not initialized, returning mock token for testing")
        return {
            'uid': 'test-user-123',
            'email': 'test@example.com',
            'name': 'Test User',
            'email_verified': True,
        }

    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except auth.InvalidIdTokenError as e:
        logger.warning(f"Invalid Firebase ID token: {e}")
    except auth.ExpiredIdTokenError as e:
        logger.warning(f"Expired Firebase ID token: {e}")
    except Exception as e:
        logger.error(f"❌ Firebase token verification failed: {e}")

    return None


def get_or_create_user_from_firebase(firebase_user):
    """
    Get or create Django user from Firebase user data
    """
    if not firebase_user or not firebase_user.get('email'):
        logger.error("Firebase user data missing email")
        raise ValueError("Firebase user must have an email")

    email = firebase_user['email'].lower().strip()

    try:
        # Try to find existing user by email (case-insensitive)
        user = User.objects.get(email__iexact=email)
        logger.info(f"Found existing user: {user.username} ({user.email})")
        return user
    except ObjectDoesNotExist:
        pass

    # Create new user
    base_username = email.split('@')[0].lower()
    username = base_username

    # Ensure username is unique
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}_{counter}"
        counter += 1

    # Handle name parsing more robustly
    full_name = firebase_user.get('name', '').strip()
    first_name = ''
    last_name = ''

    if full_name:
        name_parts = full_name.split()
        if len(name_parts) >= 1:
            first_name = name_parts[0]
        if len(name_parts) >= 2:
            last_name = ' '.join(name_parts[1:])

    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )
        logger.info(f"✅ Created new user: {user.username} ({user.email})")
        return user
    except Exception as e:
        logger.error(f"Failed to create user for {email}: {e}")
        raise


def get_firebase_user(uid):
    """
    Get Firebase user by UID
    """
    if not uid:
        logger.warning("Empty Firebase UID provided")
        return None

    try:
        firebase_user = auth.get_user(uid)
        return firebase_user
    except auth.UserNotFoundError:
        logger.warning(f"Firebase user not found: {uid}")
    except Exception as e:
        logger.error(f"❌ Failed to get Firebase user {uid}: {e}")

    return None


def is_firebase_initialized():
    """
    Check if Firebase Admin SDK is initialized
    """
    return bool(firebase_admin._apps)


# Initialize Firebase on first import
_firebase_initialized = initialize_firebase()