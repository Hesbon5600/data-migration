from django import forms
from django.contrib.auth.forms import AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field

from .models import User


class UserSignupForm(forms.ModelForm):
    """
    Signup form class
    """
    email = forms.CharField(widget=forms.TextInput(
        attrs={'placeholder': 'john.doe@email.com'}))
    password = forms.CharField(widget=forms.PasswordInput())
    first_name = forms.CharField(
        label='First Name', widget=forms.TextInput(attrs={'placeholder': 'John'}))
    last_name = forms.CharField(
        label='Last Name', widget=forms.TextInput(attrs={'placeholder': 'Doe'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.attrs = {'novalidate': ''}
        self.helper.add_input(Submit('submit', 'Signup'))


class UserLoginForm(AuthenticationForm):
    """
    Login Form class
    """
    email = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', "placeholder": "john.doe@email.com"}))
    password = forms.PasswordInput()
