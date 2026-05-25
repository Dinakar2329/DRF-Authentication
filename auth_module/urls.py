from django.contrib import admin
from django.urls import include, path
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from authentication.views import RegisterPageView
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title='Auth Module API',
        default_version='v1',
        description='API documentation for the authentication service.',
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

swagger_view = ensure_csrf_cookie(schema_view.with_ui('swagger', cache_timeout=0))

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', RegisterPageView.as_view(), name='register-page'),
    path('api/', include('authentication.urls')),
    path('swagger/', swagger_view, name='schema-swagger-ui'),
]
