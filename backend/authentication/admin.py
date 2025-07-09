from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import UserProfile
from .forms import CustomUserCreationForm, UserProfileInlineForm

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    form = UserProfileInlineForm
    can_delete = False
    verbose_name_plural = 'Profile'
    filter_horizontal = ('locations',)  # Nice UI for ManyToMany
    fk_name = 'user'

class CustomUserAdmin(DefaultUserAdmin):
    add_form = CustomUserCreationForm
    inlines = (UserProfileInline,)

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'first_name',
                'last_name',
                'password1',
                'password2',
            ),
        }),
    )

    list_display = ('username', 'get_full_name', 'get_role',)
    list_select_related = ('profile',)

    def get_full_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return '-'

    get_full_name.short_description = 'Full Name'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('profile')

    def get_role(self, obj):
        return getattr(obj.profile, 'role', '-') if hasattr(obj, 'profile') else '-'
    get_role.short_description = 'Role'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)