# authentication/admin.py

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class CustomUserAdmin(DefaultUserAdmin):
    inlines = (UserProfileInline,)

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'password1',
                'password2',
            ),
        }),
    )

    # make sure list_display still shows email & role
    list_display = ('username', 'email', 'get_role', 'is_staff')
    list_select_related = ('profile',)

    def get_role(self, obj):
        return obj.profile.role
    get_role.short_description = 'Role'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
