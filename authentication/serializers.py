import unicodedata
import hmac

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import EmailValidator
from django.db import transaction
from rest_framework import serializers

from authentication.models import RegistrationOTP
from authentication.services import create_registration_otp

User = get_user_model()

_EMAIL_MAX_LEN = 254     
_EMAIL_LOCAL_MAX_LEN = 64  
_USERNAME_MIN_LEN = 3
_USERNAME_MAX_LEN = 30
_PASSWORD_MIN_LEN = 8
_PASSWORD_MAX_LEN = 128    
_OTP_REGEX = r'^\d{6}$'

# Usernames that would cause confusion or security issues
_RESERVED_USERNAMES: frozenset[str] = frozenset({
    'admin', 'administrator', 'root', 'superuser', 'staff',
    'support', 'help', 'info', 'contact', 'abuse',
    'postmaster', 'hostmaster', 'webmaster', 'security',
    'me', 'you', 'user', 'account', 'accounts',
    'api', 'www', 'mail', 'smtp', 'ftp', 'ssh',
    'anonymous', 'guest', 'public', 'system',
    'null', 'undefined', 'none',
})

_email_validator = EmailValidator()




def _validate_email_structure(email: str) -> None:
    """Raise serializers.ValidationError for any structural email problem."""
    if not email:
        raise serializers.ValidationError('Email address is required.')

    if len(email) > _EMAIL_MAX_LEN:
        raise serializers.ValidationError(
            f'Email address must be {_EMAIL_MAX_LEN} characters or fewer.'
        )

    if email.count('@') != 1:
        raise serializers.ValidationError('Enter a valid email address.')

    local, domain = email.rsplit('@', 1)

    if not local:
        raise serializers.ValidationError('Enter a valid email address.')

    if len(local) > _EMAIL_LOCAL_MAX_LEN:
        raise serializers.ValidationError(
            'The part before @ must be 64 characters or fewer.'
        )

    if local.startswith('.') or local.endswith('.'):
        raise serializers.ValidationError('Enter a valid email address.')
    if '..' in local:
        raise serializers.ValidationError('Enter a valid email address.')

    if not domain or '.' not in domain:
        raise serializers.ValidationError('Enter a valid email address.')

    # Final authoritative check
    try:
        _email_validator(email)
    except DjangoValidationError:
        raise serializers.ValidationError('Enter a valid email address.')


class RegisterSerializer(serializers.Serializer):
    email    = serializers.EmailField(max_length=_EMAIL_MAX_LEN)
    username = serializers.CharField(
        min_length=_USERNAME_MIN_LEN,
        max_length=_USERNAME_MAX_LEN,
    )
    password = serializers.CharField(
        write_only=True,
        min_length=_PASSWORD_MIN_LEN,
        max_length=_PASSWORD_MAX_LEN,
        trim_whitespace=False, 
    )

    def validate_email(self, value: str) -> str:
        email = value.strip()
        _validate_email_structure(email)

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                'An account with this email already exists. '
                'Use "Verify account" to resend your OTP.'
            )
        return email

    def validate_username(self, value: str) -> str:
        username = value.strip()

        if not username:
            raise serializers.ValidationError('Username is required.')

        # Only ASCII letters, digits, dots, underscores, hyphens
        allowed = set('abcdefghijklmnopqrstuvwxyz'
                      'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                      '0123456789._-')
        if not all(c in allowed for c in username):
            raise serializers.ValidationError(
                'Username may only contain letters, digits, dots (.), '
                'underscores (_), and hyphens (-).'
            )

        # Must start and end with alphanumeric
        if not username[0].isascii() or not username[0].isalnum():
            raise serializers.ValidationError(
                'Username must start with a letter or digit.'
            )
        if not username[-1].isascii() or not username[-1].isalnum():
            raise serializers.ValidationError(
                'Username must end with a letter or digit.'
            )

        # No consecutive special characters (e.g. "a..b", "a--b", "a._b")
        specials = set('._-')
        for a, b in zip(username, username[1:]):
            if a in specials and b in specials:
                raise serializers.ValidationError(
                    'Username must not contain consecutive dots, hyphens, '
                    'or underscores.'
                )

        # Reserved names
        if username.lower() in _RESERVED_USERNAMES:
            raise serializers.ValidationError(
                'That username is reserved. Please choose another.'
            )

        # Case-insensitive uniqueness
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError('That username is already taken.')

        return username

    def validate_password(self, value: str) -> str:
        # Reject passwords made entirely of whitespace
        if not value.strip():
            raise serializers.ValidationError(
                'Password must contain characters other than whitespace.'
            )

        if value != value.strip():
            raise serializers.ValidationError(
                'Password must not start or end with a space.'
            )

        return value

    def validate(self, attrs: dict) -> dict:

        dummy_user = User(
            email=attrs.get('email', ''),
            username=attrs.get('username', ''),
        )
        try:
            validate_password(attrs['password'], user=dummy_user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs

    @transaction.atomic
    def save(self):
        email    = self.validated_data['email']
        username = self.validated_data['username']
        password = self.validated_data['password']

        existing = (
            User.objects.select_for_update()
            .filter(email=email)
            .first()
        )
        if existing is not None:
            raise serializers.ValidationError(
                {'email': 'An account with this email already exists.'}
            )

        user = User.objects.create(
            email=email,
            username=username,
            is_active=False,
            password=make_password(password),
        )

        create_registration_otp(email)
        return user



class RegisterVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=_EMAIL_MAX_LEN)
    otp   = serializers.RegexField(
        regex=_OTP_REGEX,
        max_length=6,
        error_messages={'invalid': 'Enter the 6-digit verification code sent to your email.'},
    )

    def validate_email(self, value: str) -> str:
        return value.strip()

    def validate_otp(self, value: str) -> str:
        return value.strip()

    def validate(self, attrs: dict) -> dict:
        email = attrs['email']
        code  = attrs['otp']

        otp_record = (
            RegistrationOTP.objects.filter(
                email=email,
                code=code,
                verified_at__isnull=True,
            )
            .order_by('-created_at')
            .first()
        )

        # Use a single generic message to avoid leaking whether the email
        # has a pending OTP at all.
        if not otp_record or otp_record.is_expired:
            raise serializers.ValidationError(
                {'otp': 'Invalid or expired verification code.'}
            )

        attrs['otp_record'] = otp_record
        return attrs



class RegisterResendSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=_EMAIL_MAX_LEN)

    def validate_email(self, value: str) -> str:
        email = value.strip()
        user = User.objects.filter(email=email).first()
        if user is None:
            # Generic message — don't reveal whether the email is registered.
            raise serializers.ValidationError(
                'If this email is registered and unverified, a new code will be sent.'
            )
        if user.is_active:
            raise serializers.ValidationError('This account is already verified.')
        return email



class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField(max_length=_EMAIL_MAX_LEN)
    password = serializers.CharField(
        write_only=True,
        max_length=_PASSWORD_MAX_LEN,
        trim_whitespace=False,
    )

    def validate_email(self, value: str) -> str:
        return value.strip()

    def validate(self, attrs: dict) -> dict:
        email    = attrs['email']
        password = attrs['password']

        user = User.objects.filter(email=email).first()

        if user is not None:
            password_ok = user.check_password(password)

        if not password_ok or user is None:
            raise serializers.ValidationError(
                {'non_field_errors': ['Invalid email or password.']}
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {'non_field_errors': ['Please verify your account before logging in.']}
            )

        attrs['user'] = user
        return attrs



class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['email', 'username', 'is_active']
        read_only_fields = fields 