import secrets

from django.conf import settings
from django.core.mail import send_mail

from authentication.models import RegistrationOTP


def create_registration_otp(email):
    code = f'{secrets.randbelow(900000) + 100000}'
    otp = RegistrationOTP.objects.create(email=email, code=code)

    send_mail(
        subject='Verify your account',
        message=f'Your verification code is {code}. It expires in 10 minutes.',
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
        recipient_list=[email],
        fail_silently=False,
    )

    return otp
