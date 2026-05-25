# Auth Module

Django authentication module with cookie-based JWT auth, registration verification, login/logout, and profile pages.

## Setup

1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. Apply migrations

```powershell
python manage.py migrate
```

4. Run the development server

```powershell
python manage.py runserver
```

## Available pages

- Registration page: `/register/`
- Login page: `/login/`
- Profile page: `/profile/`
- Swagger docs: `/swagger/`

## Registration and verification flow

- The registration page accepts `email` and `password`.
- On submit, the backend creates a pending user and sends a one-time verification code (OTP).
- The UI opens an OTP modal so the user can complete verification immediately.
- There is also a reusable verify action that prompts for email, resends the OTP, and opens the verification modal.
- Verification is completed via `POST /api/register/verify/` with `email` and `otp`.

## Authentication flow

- `POST /api/login/` logs in the user and sets two secure cookies:
  - `auth_token` (short-lived access token)
  - `refresh_token` (longer-lived refresh token)
- `POST /api/token/refresh/` uses the refresh cookie to issue a new access cookie.
- `POST /api/logout/` clears both cookies.
- `GET /api/me/` returns the authenticated user when the access cookie is valid.

## API endpoints

- `POST /api/register/`
  - Body: `email`, `password`
  - Starts registration and sends a verification OTP
- `POST /api/register/resend/`
  - Body: `email`
  - Sends a new OTP for an inactive registered user
- `POST /api/register/verify/`
  - Body: `email`, `otp`
  - Verifies the user account
- `POST /api/login/`
  - Body: `email`, `password`
  - Sets secure, HTTP-only `auth_token` and `refresh_token` cookies
- `POST /api/token/refresh/`
  - Uses the `refresh_token` cookie to issue a fresh `auth_token`
- `POST /api/logout/`
  - Clears both auth cookies
- `GET /api/me/`
  - Returns the authenticated user

## UI and template structure

- Templates extend `templates/base.html`.
- `templates/authentication/register.html` now includes reusable modal partials:
  - `templates/includes/verify_code_modal.html`
  - `templates/includes/resend_verification_modal.html`
- The registration UI opens the OTP modal automatically after a successful registration or resend action.
- Error feedback is rendered in the modal when verification or resend validation fails.

## Security and CSRF

- CSRF protection is enabled for views that render pages and for API form submissions.
- All fetch calls attach the CSRF token from the cookie.
- Cookies are set with `HttpOnly`, `Secure`, and `SameSite` flags where configured.

## Email / OTP behavior

- The default setup uses Django's console email backend and prints OTP messages to the terminal.
- To send real email, configure environment variables and settings:
  - `EMAIL_OTP_ENABLED=true`
  - `EMAIL_HOST`
  - `EMAIL_HOST_USER`
  - `EMAIL_HOST_PASSWORD`
  - `DEFAULT_FROM_EMAIL`

## Tests

- Run the authentication tests with:

```powershell
python manage.py test authentication
```

## Notes

- Static assets are served from `static/`.
- Client-side JavaScript handles OTP entry, paste support, resend flow, and verification state.
