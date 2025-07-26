from admin_interface.models import Theme
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from .models import UserProfile
from .forms import CustomUserCreationForm, UserProfileInlineForm, RequiredLocationsInlineFormSet


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    form = UserProfileInlineForm
    formset = RequiredLocationsInlineFormSet
    can_delete = False
    verbose_name_plural = 'Profile'
    filter_horizontal = ('locations',)  # Nice UI for ManyToMany
    fk_name = 'user'

class CustomUserAdmin(DefaultUserAdmin):
    add_form = CustomUserCreationForm
    inlines = (UserProfileInline,)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
    )

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

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context['show_save'] = True
        extra_context['show_save_and_add_another'] = False
        extra_context['show_save_and_continue'] = False
        extra_context['show_delete'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)

    def get_inline_instances(self, request, obj=None):
        return [inline(self.model, self.admin_site) for inline in self.inlines]

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
admin.site.unregister(Group)
admin.site.unregister(BlacklistedToken)
admin.site.unregister(OutstandingToken)
admin.site.unregister(Theme)
admin.site.register(User, CustomUserAdmin)