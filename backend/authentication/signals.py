from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Permission

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
        # Make user staff but not superuser
        if not user.is_staff:
            user.is_staff = True
            user.save(update_fields=['is_staff'])

        # Define all required permissions grouped by app
        permissions_by_app = {
            'reports': [
                # delivery report
                'add_deliveryreport', 'change_deliveryreport', 'delete_deliveryreport', 'view_deliveryreport',
                # delivery report damage image
                'add_deliveryreportdamageimage', 'change_deliveryreportdamageimage', 'delete_deliveryreportdamageimage', 'view_deliveryreportdamageimage',
                # delivery report image
                'add_deliveryreportimage', 'change_deliveryreportimage', 'delete_deliveryreportimage', 'view_deliveryreportimage',
                # delivery report item
                'add_deliveryreportitem', 'change_deliveryreportitem', 'delete_deliveryreportitem', 'view_deliveryreportitem',
                # delivery report slip image
                'add_deliveryreportslipimage', 'change_deliveryreportslipimage', 'delete_deliveryreportslipimage', 'view_deliveryreportslipimage',
                # item
                'add_item', 'change_item', 'delete_item', 'view_item',
                # location
                'add_location', 'change_location', 'delete_location', 'view_location',
                # supplier
                'add_supplier', 'change_supplier', 'delete_supplier', 'view_supplier',
            ],
            'auth': [
                'add_user', 'change_user', 'delete_user', 'view_user',
            ],
            'authentication': [
                'add_userprofile', 'change_userprofile', 'delete_userprofile', 'view_userprofile',
            ],
        }

        # Assign permissions
        for app_label, codenames in permissions_by_app.items():
            perms = Permission.objects.filter(codename__in=codenames, content_type__app_label=app_label)
            for perm in perms:
                if not user.user_permissions.filter(id=perm.id).exists():
                    user.user_permissions.add(perm)