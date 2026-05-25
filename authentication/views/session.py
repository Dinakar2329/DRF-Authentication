from django.conf import settings
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from authentication.serializers import LoginSerializer, UserDetailsSerializer

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
        token = AccessToken.for_user(user)
        response = Response(
            {
                'message': 'Login successful.',
                'user': UserDetailsSerializer(user).data,
            }
        )
        response.set_cookie(
            settings.JWT_AUTH_COOKIE_NAME,
            str(token),
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
        return response
