from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import UserProfile
from .forms import CustomUserCreationForm, UserProfileInlineForm

class NoExtraButtonsAdmin(admin.ModelAdmin):
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        # Hide "Save and add another" and "Save and continue editing"
        extra_context['show_save_and_add_another'] = False
        extra_context['show_save_and_continue'] = False
        return super().changeform_view(request, object_id, form_url, extra_context=extra_context)



class UserProfileInline(admin.StackedInline):
    model = UserProfile
    form = UserProfileInlineForm
    can_delete = False
    verbose_name_plural = 'Profile'
    filter_horizontal = ('locations',)  # Nice UI for ManyToMany
    fk_name = 'user'

class CustomUserAdmin(NoExtraButtonsAdmin, DefaultUserAdmin):
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

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)

        # Hide the "Permissions" section from staff users
        if not request.user.is_superuser:
            fieldsets = [
                (name, opts) for name, opts in fieldsets if name != 'Permissions'
            ]

        return fieldsets

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Optional: hide specific fields too, even if shown in another section
        if not request.user.is_superuser:
            for field_name in ['is_superuser', 'groups', 'user_permissions']:
                if field_name in form.base_fields:
                    form.base_fields.pop(field_name)

        return form

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)