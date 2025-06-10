# authentication/models.py
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('basic', 'Basic user'),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='basic')

@receiver(post_save, sender=UserProfile)
def ensure_staff_on_admin_profile(sender, instance, **kwargs):
    user = instance.user
    if instance.role == 'admin':
        user.is_staff = True
    else:
        user.is_staff = False
    user.save(update_fields=['is_staff', 'is_superuser'])