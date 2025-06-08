from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework.decorators import action, permission_classes

from .models import UserAPIKey
from .permissions import HasUserAPIKey
from .serializers import LoginSerializer

class AuthViewSet(viewsets.ViewSet):
    serializer_class = LoginSerializer

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    @extend_schema(
        request=LoginSerializer,
        responses={200: {
            'type': 'object',
            'properties': {
                'api_key': {'type': 'string'}
            }
        }},
        description="Login with username and password to get API key.",
        auth=[],
        tags=["Authentication"]
    )
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data["username"],
                password=serializer.validated_data["password"]
            )
            if user:
                UserAPIKey.objects.filter(user=user).delete()
                api_key, key = UserAPIKey.objects.create_key(
                    name=f"{user.username}-key",
                    user=user,
                    expiry_date=timezone.now() + timedelta(hours=1)
                )
                return Response({"api_key": key}, status=status.HTTP_200_OK)
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], permission_classes=[HasUserAPIKey], url_path="logout")
    @extend_schema(
        request=None,
        responses={200: {'type': 'object', 'properties': {'detail': {'type': 'string'}}}},
        description="Revoke the user's API key.",
        auth=["ApiKeyAuth"],
        tags=["Authentication"]
    )
    def logout(self, request):
        key = HasUserAPIKey().get_key(request)
        if not key:
            return Response({"detail": "No API key provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            prefix, secret = key.split(".", 1)
            api_key = UserAPIKey.objects.get(prefix=prefix)
        except (ValueError, UserAPIKey.DoesNotExist):
            return Response({"detail": "Invalid API key."}, status=status.HTTP_403_FORBIDDEN)

        if not api_key.is_valid(key):
            return Response({"detail": "Invalid API key."}, status=status.HTTP_403_FORBIDDEN)

        api_key.revoked = True
        api_key.save()
        return Response({"detail": "API key revoked. Logout successful."}, status=status.HTTP_200_OK)
