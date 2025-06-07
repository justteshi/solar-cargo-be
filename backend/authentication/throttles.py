from rest_framework.throttling import SimpleRateThrottle

class APIKeyRateThrottle(SimpleRateThrottle):
    scope = 'apikey'

    def get_cache_key(self, request, view):
        auth = request.headers.get("Authorization", "")
        prefix = "Api-Key "
        if auth.startswith(prefix):
            raw_key = auth[len(prefix):]
            return self.cache_format % {
                'scope': self.scope,
                'ident': raw_key
            }
        return None
