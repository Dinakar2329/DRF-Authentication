from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from authentication.models import RegistrationOTP
from authentication.services import create_registration_otp

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        email = value.lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('A user with this email already exists. To Verify Your account Use Verify Account.')
        return email

    def validate_password(self, value):
        validate_password(value)
        return value

    @transaction.atomic
    def save(self):
        email = self.validated_data['email']
        password = self.validated_data['password']

        user, _ = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'is_active': False,
            },
        )
        user.username = email
        user.email = email
        user.is_active = False
        user.set_password(password)
        user.save(update_fields=['username', 'email', 'password', 'is_active'])

        create_registration_otp(email)
        return user


class RegisterVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.RegexField(
        regex=r'^\d{6}$',
        error_messages={'invalid': 'Enter the 6-digit verification code.'},
    )

    def validate_email(self, value):
        return value.lower()

    def validate(self, attrs):
        otp = (
            RegistrationOTP.objects.filter(
                email=attrs['email'],
                code=attrs['otp'],
                verified_at__isnull=True,
            )
            .order_by('-created_at')
            .first()
        )

        if not otp or otp.is_expired:
            raise serializers.ValidationError('Invalid or expired verification code.')

        attrs['otp_record'] = otp
        return attrs


class RegisterResendSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        email = value.lower()
        user = User.objects.filter(email=email).first()
        if user is None:
            raise serializers.ValidationError('No registration found for this email.')
        if user.is_active:
            raise serializers.ValidationError('This account is already verified.')
        return email


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        return value.lower()

    def validate(self, attrs):
        user = authenticate(
            username=attrs['email'],
            password=attrs['password'],
        )
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        if not user.is_active:
            raise serializers.ValidationError('Please verify your account before logging in.')

        attrs['user'] = user
        return attrs


class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'username', 'is_active']
