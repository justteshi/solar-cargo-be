from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from .permissions import HasUserAPIKey
from .models import UserAPIKey

class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        raw = HasUserAPIKey().get_key(request)
        if not raw:
            return None

        try:
            prefix, secret = raw.split(".", 1)
            api_key = UserAPIKey.objects.get(prefix=prefix)
        except (ValueError, UserAPIKey.DoesNotExist):
            raise exceptions.AuthenticationFailed("Invalid API key.")

        if not api_key.is_valid(raw):
            raise exceptions.AuthenticationFailed("Invalid API key.")

        if api_key.revoked:
            raise exceptions.AuthenticationFailed("This API key has been revoked.")

        return (api_key.user, api_key)
