# Auth Module

Small Django REST API project for authentication-related endpoints.

## Local setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Swagger UI is available at `/swagger/` and sets a CSRF cookie on page load.
Registration page is available at `/register/`.

## Registration

- `POST /api/register/` with `email` and `password` starts registration and sends an OTP.
- `POST /api/register/verify/` with `email` and `otp` verifies the account.
- `POST /api/login/` with `email` and `password` sets the HTTP-only `auth_token` cookie.
- `GET /api/me/` returns the logged-in user and requires the `auth_token` cookie.

By default OTP emails use Django's console backend and print in the terminal.
Set `EMAIL_OTP_ENABLED=true` with `EMAIL_HOST`, `EMAIL_HOST_USER`,
`EMAIL_HOST_PASSWORD`, and `DEFAULT_FROM_EMAIL` to send real email.
