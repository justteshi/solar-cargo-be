# authentication/middleware.py

from django.http import JsonResponse
from rest_framework.throttling import SimpleRateThrottle, AnonRateThrottle
from .throttles import APIKeyRateThrottle

class GlobalRateThrottleMiddleware:
    """
    Rate-limiting преди permission check:
      - ако има Api-Key header ➔ throttle-ваш с APIKeyRateThrottle
      - иначе ➔ throttle-ваш с AnonRateThrottle
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.api_throttle  = APIKeyRateThrottle()
        self.anon_throttle = AnonRateThrottle()

    def __call__(self, request):
        # само за DRF API пътища
        if request.path.startswith("/api/"):
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Api-Key "):
                if not self.api_throttle.allow_request(request, None):
                    return JsonResponse(
                        {"detail": "Rate limit exceeded for API key."},
                        status=429
                    )
            else:
                if not self.anon_throttle.allow_request(request, None):
                    return JsonResponse(
                        {"detail": "Rate limit exceeded for anonymous user."},
                        status=429
                    )

        # ако мине throttle-а, продължаваме към нормалния DRF flow
        return self.get_response(request)
