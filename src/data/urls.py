
from django.urls import path

from .views import UserRegistrationCreateView, UserLoginCreateView


urlpatterns = [
    path('signup', UserRegistrationCreateView.as_view(), name='user-registration'),
    path('login', UserLoginCreateView.as_view(), name='user-login'),
]