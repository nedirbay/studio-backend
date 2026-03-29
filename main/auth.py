import jwt
from django.conf import settings
from rest_framework import authentication
from rest_framework import exceptions

from .models import User


class StudioJWTAuthentication(authentication.BaseAuthentication):
    """
    Simple JWT auth that validates HS256 tokens we issue and returns our business User.
    """

    def authenticate(self, request):
        auth = authentication.get_authorization_header(request).decode("utf-8")
        if not auth or not auth.lower().startswith("bearer "):
            return None
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.PyJWTError:
            raise exceptions.AuthenticationFailed("Invalid token")
        if payload.get("type") != "access":
            raise exceptions.AuthenticationFailed("Access token required")
        user_id = payload.get("user_id")
        if not user_id:
            raise exceptions.AuthenticationFailed("Invalid payload")
        user = User.objects.filter(id=user_id, is_active=True).first()
        if not user:
            raise exceptions.AuthenticationFailed("User not found")
        return (user, None)
