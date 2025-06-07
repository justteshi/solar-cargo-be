from rest_framework.throttling import SimpleRateThrottle
from django.http import JsonResponse


class APIKeyHeaderThrottle(SimpleRateThrottle):
    scope = "api_key_header"

    def get_cache_key(self, request, view):
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Api-Key "):
            raw_key = auth[len("Api-Key "):]
            return self.cache_format % {
                'scope': self.scope,
                'ident': raw_key
            }
        return None


class SoftThrottleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.throttle = APIKeyHeaderThrottle()

    def __call__(self, request):
        if request.path.startswith("/api/"):
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Api-Key "):
                if not self.throttle.allow_request(request, None):
                    return JsonResponse(
                        {"detail": "Rate limit exceeded. Too many requests."},
                        status=429
                    )
        return self.get_response(request)