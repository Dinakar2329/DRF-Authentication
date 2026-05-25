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

## API endpoints

- `POST /api/register/`
  - Body: `email`, `password`
  - Starts registration and sends a verification OTP
- `POST /api/register/verify/`
  - Body: `email`, `otp`
  - Verifies the user account
- `POST /api/login/`
  - Body: `email`, `password`
  - Sets a secure, HTTP-only `auth_token` cookie
- `POST /api/logout/`
  - Clears the `auth_token` cookie
- `GET /api/me/`
  - Returns the authenticated user
  - Requires the `auth_token` cookie

## Notes

- CSRF protection is enabled for form submissions and API requests.
- The Swagger UI sets a CSRF cookie when loaded.
- The auth cookie is stored as `auth_token` and is HttpOnly.
- Static assets are served from `static/` and templates extend `templates/base.html`.

## Email / OTP behavior

By default the project uses Django's console email backend and prints OTP messages to the terminal.

To send real email, configure environment variables and update settings accordingly:

- `EMAIL_OTP_ENABLED=true`
- `EMAIL_HOST`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`

## Development tips

- Use `python manage.py runserver` to start the app locally.
- Use the browser to visit `/register/` and `/login/` for the UI flows.
- Verify authenticated access by visiting `/profile/` after login.
