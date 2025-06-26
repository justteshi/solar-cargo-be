from django.contrib.auth import get_user_model


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