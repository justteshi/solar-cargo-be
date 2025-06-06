from rest_framework_api_key.permissions import BaseHasAPIKey
from .models import UserAPIKey

class HasUserAPIKey(BaseHasAPIKey):
    model = UserAPIKey

    def get_key(self, request):
        auth = request.headers.get("Authorization", "")
        prefix = "Api-Key "
        if auth.startswith(prefix):
            return auth[len(prefix):]
        return None