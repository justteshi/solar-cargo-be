# authentication/throttles.py

from rest_framework.throttling import SimpleRateThrottle

class JWTUserThrottle(SimpleRateThrottle):
    scope = 'jwt'

    def get_cache_key(self, request, view):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            # throttle-вай по user ID
            return self.cache_format % {'scope': self.scope, 'ident': user.pk}
        return None


class AnonIPThrottle(SimpleRateThrottle):
    scope = 'anon'

    def get_cache_key(self, request, view):
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Api-Key "):
            return None

        ident = request.META.get('REMOTE_ADDR')
        if ident:
            return self.cache_format % {
                'scope': self.scope,
                'ident': ident
            }
        return None
