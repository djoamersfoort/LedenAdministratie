from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseForbidden
from oauth2_provider.views import ClientProtectedResourceView


class PermissionRequiredMixin(UserPassesTestMixin):
    required_permission = "LedenAdministratie.view_member"

    def check_user(self, user):
        if (
            user.is_authenticated
            and user.has_perm(self.required_permission)
            and user.is_active
        ):
            return True
        return False

    def test_func(self):
        return self.check_user(self.request.user)


class AllowListedClientCredentialsMixin(ClientProtectedResourceView):
    allowed_client_ids = []

    def dispatch(self, request, *args, **kwargs):
        if request.method.upper() == "OPTIONS":
            return super().dispatch(request, *args, **kwargs)

        # Set by oauth2_provider.middleware.OAuth2ExtraTokenMiddleware
        if not hasattr(request, "access_token"):
            return HttpResponseForbidden()

        client_id = request.access_token.application.client_id
        if client_id not in self.allowed_client_ids:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)
