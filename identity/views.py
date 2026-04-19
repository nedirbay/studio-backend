from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random

from .models import User, OTPCode, Role
from .serializers import UserRegisterSerializer, UserLoginSerializer, UserSerializer, AdminUserSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser

class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = AdminUserSerializer
    # Temporarily allow any or require Auth, ideally IsAdminUser
    # Given the frontend is sending the token, IsAdminUser is best if they are superuser or staff.
    # For now, IsAuthenticated since our custom Role-based admin might not use is_staff.
    permission_classes = [IsAuthenticated]


def _send_otp_email(user, code):
    subject = 'Giriş üçin tassyklama kody'
    message = f'Salam {user.username},\n\nSiziň tassyklama kodyňyz: {code}\n\nBu kod 10 minut dowamynda güýjini saklaýar.'
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        print(f"Email sent successfully to {user.email}")
        return True
    except Exception as e:
        print(f"CRITICAL: Email sending failed: {e}")
        return False

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = UserRegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # Create user but ensure it is INACTIVE
            user = serializer.save()
            user.is_active = False
            user.is_email_verified = False
            
            # Default role assignment
            customer_role = Role.objects.filter(name='Customer').first()
            if customer_role:
                user.role = customer_role
            
            user.save()

            # Generate and save OTP
            code = f"{random.randint(100000, 999999)}"
            expires = timezone.now() + timedelta(minutes=10)
            OTPCode.objects.create(user=user, code=code, expires_at=expires)
            
            # Send Email
            _send_otp_email(user, code)

        return Response({
            "message": "Tassyklama kody e-poçtaňyza ugradyldy",
            "email": user.email
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        print(f"Registration error: {e}")
        return Response({"error": "Hasaba alynmakda ýalňyşlyk ýüze çykdy"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp_view(request):
    email = str(request.data.get("email", "")).strip()
    code = str(request.data.get("code", "")).strip()

    print(f"--- OTP Verification Attempt ---")
    print(f"Email: {email}, Code: {code}")

    if not all([email, code]):
        return Response({"error": "E-poçta we kod gerek"}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(email=email).first()
    if not user:
        print(f"User not found for email: {email}")
        return Response({"error": "Ulanyjy tapylmady"}, status=status.HTTP_404_NOT_FOUND)

    # Find the latest OTP for this user and code
    otp_record = OTPCode.objects.filter(user=user, code=code).order_by('-created_at').first()
    
    if not otp_record:
        print(f"No OTP record found for user {user.username} with code {code}")
        # Let's see what codes ARE there
        all_codes = list(OTPCode.objects.filter(user=user).values_list('code', flat=True))
        print(f"Available codes for user: {all_codes}")
        return Response({"error": "Kod nädogry ýa-da möwriti öten"}, status=status.HTTP_400_BAD_REQUEST)

    now = timezone.now()
    valid = otp_record.is_valid()
    print(f"OTP Record: {otp_record.code}, Expires: {otp_record.expires_at}, Now: {now}")
    print(f"Is Valid: {valid}")

    if not valid:
        return Response({"error": "Kod nädogry ýa-da möwriti öten"}, status=status.HTTP_400_BAD_REQUEST)

    # Success - Activate User
    user.is_active = True
    user.is_email_verified = True
    user.save()

    otp_record.delete() # Cleanup

    refresh = RefreshToken.for_user(user)
    return Response({
        "user": UserSerializer(user).data,
        "jwt": str(refresh.access_token),
        "refresh": str(refresh)
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp_view(request):
    email = request.data.get("email")
    if not email:
        return Response({"error": "E-poçta gerek"}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(email=email, is_email_verified=False).first()
    if not user:
        return Response({"error": "Ulanyjy tapylmady ýa-da eýýäm tassyklanan"}, status=status.HTTP_404_NOT_FOUND)

    code = f"{random.randint(100000, 999999)}"
    expires = timezone.now() + timedelta(minutes=10)
    OTPCode.objects.create(user=user, code=code, expires_at=expires)
    
    if _send_otp_email(user, code):
        return Response({"message": "Täze kod ugradyldy"})
    return Response({"error": "E-poçta ugratmak başartmady"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        if user:
            if not user.is_active:
                return Response({'error': 'Hasabyňyz tassyklanmady. E-poçtaňyzy barlaň'}, status=status.HTTP_403_FORBIDDEN)
            
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'jwt': str(refresh.access_token),
                'refresh': str(refresh)
            })
        return Response({'error': 'Ulanyjy ady ýa-da parol nädogry'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def me_view(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

from .models import Notification
from .serializers import NotificationSerializer

@api_view(['GET'])
def notifications_view(request):
    """Get all notifications for the current user."""
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    return Response(NotificationSerializer(notifs, many=True).data)

@api_view(['PUT'])
def mark_notifications_read(request):
    """Mark all unread notifications as read for the user."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({"success": True})

@api_view(['DELETE'])
def delete_notification(request, notif_id):
    try:
        Notification.objects.filter(id=notif_id, user=request.user).delete()
        return Response({"success": True})
    except Exception as e:
        return Response({"error": str(e)}, status=400)
