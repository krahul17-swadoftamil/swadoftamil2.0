"""
Custom JWT serializers for Firebase authentication
"""

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class FirebaseTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that accepts Firebase ID tokens
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove default username/password fields
        self.fields.pop('username', None)
        self.fields.pop('password', None)
        # Add Firebase token field
        self.fields['id_token'] = serializers.CharField()

    def validate(self, attrs):
        """
        Validate Firebase ID token and return JWT tokens
        """
        from .firebase_utils import verify_firebase_token, get_or_create_user_from_firebase
        
        id_token = attrs.get('id_token')

        if not id_token:
            raise self.fail('no_token', 'Firebase ID token is required')

        # Verify Firebase token
        firebase_user = verify_firebase_token(id_token)

        if not firebase_user:
            raise self.fail('invalid_token', 'Invalid Firebase token')

        # Get or create Django user
        user = get_or_create_user_from_firebase(firebase_user)

        if not user or not user.is_active:
            raise self.fail('inactive_user', 'User account is disabled')

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        data = {
            'refresh': str(refresh),
            'access': str(access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }

        return data

    @classmethod
    def get_token(cls, user):
        """
        Override to return custom token
        """
        return RefreshToken.for_user(user)

    def fail(self, key, message):
        """
        Helper method to raise validation errors
        """
        from rest_framework.exceptions import ValidationError
        raise ValidationError({key: [message]})


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that includes user data in response
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add user data to response
        user = self.user
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }

        return data