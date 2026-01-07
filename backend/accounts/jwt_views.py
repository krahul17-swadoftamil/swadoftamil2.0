"""
Custom JWT views for Firebase authentication
"""

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework import status
from .jwt_serializers import FirebaseTokenObtainPairSerializer, CustomTokenObtainPairSerializer


class FirebaseTokenObtainPairView(TokenObtainPairView):
    """
    JWT token view that accepts Firebase ID tokens
    """
    serializer_class = FirebaseTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """
        Handle Firebase token authentication and return JWT tokens
        """
        return Response({"message": "Firebase endpoint working"}, status=status.HTTP_200_OK)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token view that includes user data
    """
    serializer_class = CustomTokenObtainPairSerializer