from django.urls import path

from authentication.views import (
    LoginView,
    LogoutView,
    MeView,
    RefreshTokenView,
    RegisterResendView,
    RegisterVerifyView,
    RegisterView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('register/resend/', RegisterResendView.as_view(), name='register-resend'),
    path('register/verify/', RegisterVerifyView.as_view(), name='register-verify'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
]
