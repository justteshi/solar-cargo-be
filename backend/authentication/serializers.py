from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import UserProfile

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        help_text="Valid refresh token to blacklist"
    )

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['userName'] = user.username
        token['userRole'] = getattr(user, 'role', None)
        return token

class TokenResponseSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access  = serializers.CharField()

class AccessSerializer(serializers.Serializer):
    access = serializers.CharField()

class LogoutResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()

class ProfilePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']