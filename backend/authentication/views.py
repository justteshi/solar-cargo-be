# backend/authentication/views.py

from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from .serializers import LoginSerializer, LogoutSerializer, LogoutResponseSerializer, AccessSerializer, \
    TokenResponseSerializer


User = get_user_model()
@extend_schema(tags=['Authentication'])
class AuthViewSet(viewsets.ViewSet):
    serializer_action_classes = {
        'login':   LoginSerializer,
        'refresh': TokenRefreshSerializer,
        'logout':  LogoutSerializer,
    }

    def get_serializer_class(self):
        return self.serializer_action_classes.get(self.action)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='login')
    @extend_schema(
        request=LoginSerializer,
        responses={200: TokenResponseSerializer},
    )
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data['username']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(Q(username=identifier) | Q(email=identifier))
        except User.DoesNotExist:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        refresh['userName'] = user.username
        refresh['userRole'] = getattr(user.profile, 'role', None)

        # Optional: Add full name if both first and last name exist
        if user.first_name and user.last_name:
            refresh['fullName'] = f"{user.first_name} {user.last_name}"

        # 🔥 Add locations if assigned
        profile = getattr(user, 'profile', None)
        if profile:
            locations = profile.locations.all()
            if locations.exists():
                # Add list of location names, or adjust to include more fields if needed
                refresh['locations'] = [{'id': loc.id, 'name': loc.name} for loc in locations]

        access = refresh.access_token

        return Response({
            'refresh': str(refresh),
            'access': str(access),
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='refresh')
    @extend_schema(
        request=TokenRefreshSerializer,
        responses={200: AccessSerializer},
    )
    def refresh(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            raise AuthenticationFailed("Invalid or missing refresh token.")

        return Response(
            {'access': serializer.validated_data['access']},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='logout')
    @extend_schema(
        request=LogoutSerializer,
        responses={200: LogoutResponseSerializer},
        auth=['bearerAuth'],
    )
    def logout(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_str = serializer.validated_data['refresh']
        try:
            token = RefreshToken(token_str)
            token.blacklist()
        except Exception:
            return Response({'detail': 'Invalid or already blacklisted token'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response({'detail': 'Logout successful. Refresh token blacklisted.'},
                        status=status.HTTP_200_OK)
