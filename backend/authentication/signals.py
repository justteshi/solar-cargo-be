from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'profile'):
        role = 'admin' if instance.is_superuser else 'basic'
        UserProfile.objects.create(user=instance, role=role)

@receiver(post_save, sender=UserProfile)
def ensure_staff_on_admin_profile(sender, instance, **kwargs):
    user = instance.user

    if instance.role == 'admin':
        user.is_staff = True
        user.is_superuser = True
        user.save(update_fields=['is_staff', 'is_superuser'])