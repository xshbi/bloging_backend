from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView,
    ProfileView,
    PublicProfileView,
    ChangePasswordView,
    LogoutView,
    AllUsersView,
    OAuthSuccessView
)

urlpatterns = [
    # Auth
    path('register/',         RegisterView.as_view(),       name='register'),
    path('login/',            TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/',    TokenRefreshView.as_view(),    name='token_refresh'),
    path('logout/',           LogoutView.as_view(),          name='logout'),
    path('oauth/success/',    OAuthSuccessView.as_view(),    name='oauth_success'),

    # Profile
    path('profile/',                      ProfileView.as_view(),       name='profile'),
    path('profile/change-password/',      ChangePasswordView.as_view(), name='change_password'),
    path('profile/<str:username>/',       PublicProfileView.as_view(), name='public_profile'),

    # Admin only
    path('all/',              AllUsersView.as_view(),        name='all_users'),
]