# authentication/models.py
from django.conf import settings
from django.db import models
from reports.models import Location

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
    locations = models.ManyToManyField(Location, blank= True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    signature = models.ImageField(upload_to='signatures/', null=True, blank=True)