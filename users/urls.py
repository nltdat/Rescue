from django.urls import path
from .views import (
    RegisterAPIView, 
    LoginView, 
    LogoutView, 
    TokenRefreshAPIView,
    MeView, 
    UserListView
)

app_name = 'users'

urlpatterns = [
    path('auth/register/', RegisterAPIView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshAPIView.as_view(), name='token_refresh'),

    path('users/me/', MeView.as_view(), name='me'),
    path('users/', UserListView.as_view(), name='user-list'),
]
