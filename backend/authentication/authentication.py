from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication

class APIKeyFallbackAuthentication(BaseAuthentication):
    def authenticate(self, request):
        return AnonymousUser(), None