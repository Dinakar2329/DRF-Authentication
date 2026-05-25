from django.urls import path

from authentication.views import LoginView, LogoutView, MeView, RegisterVerifyView, RegisterView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('register/verify/', RegisterVerifyView.as_view(), name='register-verify'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
]
