from django.contrib.auth import get_user_model
from authentication.models import UserProfile


def get_username_from_id(user_id):
    """
    Return the full name for a user ID, or username if full name is blank.
    """
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
        full_name = user.get_full_name()
        return full_name if full_name.strip() else user.username
    except User.DoesNotExist:
        return "Unknown User"


def get_signature_from_user_id(user_id):
    """
    Return the signature URL for a user ID, or None if not found.
    """
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
        profile = UserProfile.objects.get(user=user)
        if profile.signature:
            return profile.signature.url
        return None
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        return None
