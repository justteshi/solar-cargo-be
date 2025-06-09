# backend/authentication/urls.py
from django.urls import path
from .views import AuthViewSet

urlpatterns = [
    path('login',   AuthViewSet.as_view({'post': 'login'}),   name='auth-login'),
    path('logout',  AuthViewSet.as_view({'post': 'logout'}),  name='auth-logout'),
    path('refresh', AuthViewSet.as_view({'post': 'refresh'}), name='auth-refresh'),
]