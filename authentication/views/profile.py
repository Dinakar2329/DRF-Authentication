from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView

from authentication.authentication import CookieJWTAuthentication


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ProfilePageView(TemplateView):
    template_name = 'authentication/profile.html'

    def dispatch(self, request, *args, **kwargs):
        auth_result = CookieJWTAuthentication().authenticate(request)
        if auth_result is None:
            return redirect('login-page')

        request.user, request.auth = auth_result
        return super().dispatch(request, *args, **kwargs)
