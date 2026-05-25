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
