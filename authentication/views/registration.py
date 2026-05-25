from smtplib import SMTPException

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.serializers import RegisterSerializer, RegisterVerifySerializer

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

User = get_user_model()


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RegisterPageView(TemplateView):
    template_name = 'authentication/register.html'


@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginPageView(TemplateView):
    template_name = 'authentication/login.html'


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={201: openapi.Response('Registration successful')},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except SMTPException:
            return Response(
                {'detail': 'Could not send verification email. Please try again later.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {'message': 'Registration started. Please check your email for the OTP.'},
            status=status.HTTP_201_CREATED,
        )


class RegisterVerifyView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=RegisterVerifySerializer,
        responses={200: openapi.Response('Registration verification successful')},
    )
    @transaction.atomic
    def post(self, request):
        serializer = RegisterVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp_record']
        user = User.objects.filter(email=email).first()
        if not user:
            return Response(
                {'detail': 'Registration request not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        user.is_active = True
        user.save(update_fields=['is_active'])

        otp.verified_at = timezone.now()
        otp.save(update_fields=['verified_at'])

        return Response({'message': 'Registration completed successfully.'})
