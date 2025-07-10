from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet
from django_select2.forms import Select2MultipleWidget
from django.contrib.auth.models import User
from .models import UserProfile

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

    def clean_locations(self):
        locations = self.cleaned_data.get('locations')
        if not locations:
            raise ValidationError("Assign location for the user.")
        return locations

class RequiredLocationsInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if self.instance.pk is None:
            has_locations = False
            for form in self.forms:
                if not form.cleaned_data or form.cleaned_data.get('DELETE', False):
                    continue
                if form.cleaned_data.get('locations'):
                    has_locations = True
                    break

            if not has_locations:
                raise ValidationError("Please assign at least one location for the user.")