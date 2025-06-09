# authentication/middleware.py
from .throttles import AnonIPThrottle, JWTUserThrottle
from django.http import JsonResponse

class GlobalRateThrottleMiddleware:
    def __init__(self, get_response):
        self.get_response   = get_response
        self.anon_throttle  = AnonIPThrottle()
        self.jwt_throttle   = JWTUserThrottle()

    def __call__(self, request):
        if request.path.startswith('/api/'):
            auth = request.headers.get('Authorization', '')

            if auth.startswith('Bearer '):
                if not self.jwt_throttle.allow_request(request, None):
                    return JsonResponse({'detail': 'JWT rate limit exceeded.'}, status=429)

            else:
                if not self.anon_throttle.allow_request(request, None):
                    return JsonResponse({'detail': 'Anonymous rate limit exceeded.'}, status=429)

        return self.get_response(request)
