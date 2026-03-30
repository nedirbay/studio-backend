from datetime import datetime, timedelta
from decimal import Decimal

import jwt
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from auth.models import User
from .services import AuthService

auth_service = AuthService()


def _user_from_request(request):
    if hasattr(request, "user") and getattr(request, "user").is_authenticated:
        return request.user
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
    elif auth_header.lower().startswith("token "):
        token = auth_header.split(" ", 1)[1]
    elif "token" in request.GET:
        token = request.GET.get("token")
    if not token:
        return None
    # Try JWT first
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if user_id:
            return User.objects.filter(id=user_id, is_active=True).select_related("role").first()
    except jwt.PyJWTError:
        pass
    # fallback to legacy token auth
    return auth_service.login(token)


def _issue_jwt(user: User, minutes: int = 30, token_type: str = "access"):
    exp = datetime.utcnow() + timedelta(minutes=minutes)
    payload = {
        "type": token_type,
        "user_id": user.id,
        "role": user.role.name if user.role else None,
        "exp": exp,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token


def _issue_refresh_jwt(user: User, days: int = 7):
    return _issue_jwt(user, minutes=days * 24 * 60, token_type="refresh")


@api_view(["POST"])
@permission_classes([AllowAny])
def auth_login(request):
    data = request.data
    token = data.get("token")
    if not token:
        return Response({"error": "token required"}, status=status.HTTP_400_BAD_REQUEST)
    user = auth_service.login(token)
    if not user:
        return Response({"error": "invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
    jwt_token = _issue_jwt(user)
    refresh = _issue_refresh_jwt(user)
    return Response(
        {
            "id": user.id,
            "name": user.name,
            "role": user.role.name if user.role else None,
            "salary": float(user.salary),
            "phone": user.phone,
            "avatar_path": user.avatar_path,
            "jwt": jwt_token,
            "refresh": refresh,
        }
    )


@api_view(["GET"])
def auth_me(request):
    user = _user_from_request(request)
    if not user:
        return Response({"error": "unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(
        {
            "id": user.id,
            "name": user.name,
            "role": user.role.name if user.role else None,
            "salary": float(user.salary),
            "phone": user.phone,
            "avatar_path": user.avatar_path,
        }
    )


@api_view(["PUT"])
def auth_profile(request):
    user = _user_from_request(request)
    if not user:
        return Response({"error": "unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    data = request.data
    allowed_fields = {"name", "phone", "avatar_path", "salary", "is_active"}
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    if "salary" in update_data:
        update_data["salary"] = Decimal(str(update_data["salary"]))
    updated = auth_service.update_profile(user.id, update_data)
    return Response({"updated": updated})


@api_view(["POST"])
@permission_classes([AllowAny])
def auth_refresh(request):
    refresh_token = request.data.get("refresh")
    if not refresh_token:
        return Response({"error": "refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            return Response({"error": "invalid token type"}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(id=payload.get("user_id"), is_active=True).first()
        if not user:
            return Response({"error": "user not found"}, status=status.HTTP_401_UNAUTHORIZED)
        new_access = _issue_jwt(user)
        new_refresh = _issue_refresh_jwt(user)
        return Response({"jwt": new_access, "refresh": new_refresh})
    except jwt.ExpiredSignatureError:
        return Response({"error": "refresh expired"}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.PyJWTError:
        return Response({"error": "invalid token"}, status=status.HTTP_400_BAD_REQUEST)
