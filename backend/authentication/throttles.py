# authentication/throttles.py

from rest_framework.throttling import SimpleRateThrottle

class APIKeyRateThrottle(SimpleRateThrottle):
    scope = 'apikey'

    def get_cache_key(self, request, view):
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Api-Key "):
            raw_key = auth[len("Api-Key "):]
            return self.cache_format % {
                'scope': self.scope,
                'ident': raw_key
            }
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
