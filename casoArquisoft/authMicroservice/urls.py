from django.urls import path
from .views import register_view, oauth0_login_view, oauth0_callback_view

app_name = 'auth'

urlpatterns = [
    path('register/', register_view, name='register'),
    path('oauth0/login/', oauth0_login_view, name='oauth0_login'),
    path('oauth0/callback/', oauth0_callback_view, name='oauth0_callback'),
]
