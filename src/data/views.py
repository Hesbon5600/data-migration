from django.views.generic import CreateView, FormView
from django.conf import settings
from django.shortcuts import render, redirect, reverse
from django.contrib.auth import authenticate, login
from django.contrib import messages

from .models import User
from .forms import UserSignupForm, UserLoginForm


class UserRegistrationCreateView(FormView):
    """
    Create user api view
    """
    model = User
    form_class = UserSignupForm
    template_name = settings.SIGNUP_FORM

    def post(self, request):
        """
        Overide the default post()
        """
        form = self.form_class(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})
        data = {
            "first_name": form.cleaned_data['first_name'],
            "last_name": form.cleaned_data['last_name'],
            "password": form.cleaned_data['password'],
            "email": form.cleaned_data['email'],
            "age": form.cleaned_data['age'],
        }
        User.objects.create_user(**data)
        return redirect(reverse('user-login'))


class UserLoginCreateView(FormView):
    """
    Create user api view
    """
    model = User
    form_class = UserLoginForm
    template_name = settings.LOGIN_FORM
    success_url = "/scenarios"

    def post(self, request):
        """
        Overide the default post()
        """
        form = self.form_class(request.POST)
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user and user.is_active:
            login(request, user)
            return super(UserLoginCreateView, self).form_valid(form)
        messages.success(request, 'Wrong credentials', extra_tags='red')
        return render(request, self.template_name, {"form": form})
