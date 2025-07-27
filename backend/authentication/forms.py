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