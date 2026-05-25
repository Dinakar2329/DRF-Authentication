from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from authentication.serializers import LoginSerializer, UserDetailsSerializer

User = get_user_model()

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={200: openapi.Response('Login successful and auth cookie set')},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        access_token = AccessToken.for_user(user)
        refresh_token = RefreshToken.for_user(user)
        response = Response(
            {
                'message': 'Login successful.',
                'user': UserDetailsSerializer(user).data,
            }
        )
        response.set_cookie(
            settings.JWT_AUTH_COOKIE_NAME,
            str(access_token),
            max_age=settings.JWT_AUTH_COOKIE_MAX_AGE,
            httponly=True,
            secure=settings.JWT_AUTH_COOKIE_SECURE,
            samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
        )
        response.set_cookie(
            settings.JWT_AUTH_REFRESH_COOKIE_NAME,
            str(refresh_token),
            max_age=settings.JWT_AUTH_REFRESH_COOKIE_MAX_AGE,
            httponly=True,
            secure=settings.JWT_AUTH_COOKIE_SECURE,
            samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
        )
        return response


class RefreshTokenView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        responses={200: openapi.Response('Access token refreshed')},
    )
    def post(self, request):
        raw_refresh_token = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE_NAME)
        if raw_refresh_token is None:
            return Response({'detail': 'Refresh token missing.'}, status=401)

        try:
            refresh_token = RefreshToken(raw_refresh_token)
            user_id = refresh_token['user_id']
        except TokenError:
            return Response({'detail': 'Refresh token invalid or expired.'}, status=401)

        user = User.objects.filter(id=user_id).first()
        if user is None:
            return Response({'detail': 'User not found.'}, status=401)

        access_token = AccessToken.for_user(user)
        response = Response({'message': 'Access token refreshed.'})
        response.set_cookie(
            settings.JWT_AUTH_COOKIE_NAME,
            str(access_token),
            max_age=settings.JWT_AUTH_COOKIE_MAX_AGE,
            httponly=True,
            secure=settings.JWT_AUTH_COOKIE_SECURE,
            samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
        )
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserDetailsSerializer(request.user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: openapi.Response('Logged out successfully')},
    )
    def post(self, request):
        response = Response({'message': 'Logged out successfully.'})
        response.delete_cookie(
            settings.JWT_AUTH_COOKIE_NAME,
            samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
        )
        response.delete_cookie(
            settings.JWT_AUTH_REFRESH_COOKIE_NAME,
            samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
        )
        return response
