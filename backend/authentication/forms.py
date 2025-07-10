from django import forms
from django.contrib.auth.forms import UserCreationForm
from django_select2.forms import Select2MultipleWidget
from django.contrib.auth.models import User
from .models import UserProfile
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

class UserProfileInlineForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = '__all__'
        widgets = {
            'locations': Select2MultipleWidget,
        }

class RequiredLocationsInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            if not form.cleaned_data.get('DELETE', False):
                locations = form.cleaned_data.get('locations')
                if not locations or locations.count() == 0:
                    raise ValidationError("You must select at least one location for the user.")
