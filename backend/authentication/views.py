from django.db.models import Q
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework.views import APIView
from .serializers import (
    LoginSerializer,
    LogoutSerializer,
    LogoutResponseSerializer,
    AccessSerializer,
    TokenResponseSerializer,
    ProfilePictureSerializer
)


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
                refresh['locations'] = [{'id': loc.id, 'name': loc.name, 'client_name': loc.client_name} for loc in locations]

        # Add userPicture URL if exists
        if profile and profile.profile_picture:
            # This builds the full URL for the profile_picture (works locally and with S3 if MEDIA_URL is properly configured)
            user_picture_url = request.build_absolute_uri(profile.profile_picture.url)
            refresh['userPicture'] = user_picture_url

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

class UploadProfilePictureView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'profile_picture': {
                        'type': 'string',
                        'format': 'binary'
                    }
                },
                'required': ['profile_picture']
            }
        },
        tags=['Profile'],
        responses={
            200: OpenApiResponse(description="Profile picture updated.")
        }
    )
    def patch(self, request, *args, **kwargs):
        profile = request.user.profile
        new_image = request.FILES.get('profile_picture')
        # 🧹 Delete old image safely, even on S3
        if new_image and profile.profile_picture:
            profile.profile_picture.delete(save=False)

        serializer = ProfilePictureSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Profile picture updated successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)