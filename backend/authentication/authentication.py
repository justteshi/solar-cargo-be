from django.core.cache import cache
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions

from .permissions import HasUserAPIKey
from .models import UserAPIKey

class APIKeyAuthentication(BaseAuthentication):
    CACHE_TTL = 60  # секунди

    def authenticate(self, request):
        raw = HasUserAPIKey().get_key(request)
        if not raw:
            return None

        try:
            prefix, secret = raw.split(".", 1)
        except ValueError:
            raise exceptions.AuthenticationFailed("Invalid API key format.")

        cache_key = f"api_key_obj:{prefix}"
        api_key = cache.get(cache_key)

        if api_key is None:
            try:
                api_key = UserAPIKey.objects.get(prefix=prefix)
            except UserAPIKey.DoesNotExist:
                raise exceptions.AuthenticationFailed("Invalid API key.")
            cache.set(cache_key, api_key, self.CACHE_TTL)

        if getattr(api_key, "expiry", None) and api_key.expiry < timezone.now():
            raise exceptions.AuthenticationFailed("API key has expired.")

        if not api_key.is_valid(raw):
            raise exceptions.AuthenticationFailed("Invalid API key.")

        if api_key.revoked:
            raise exceptions.AuthenticationFailed("This API key has been revoked.")

        return (api_key.user, api_key)
