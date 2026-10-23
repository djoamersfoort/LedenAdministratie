from django.conf import settings
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
    allowed_client_ids: list[str] | None = None

    def get_allowed_client_ids(self):
        if self.allowed_client_ids is not None:
            return self.allowed_client_ids
        return getattr(settings, "SMOELENBOEK_API_ALLOWED_CLIENTS", [])

    def dispatch(self, request, *args, **kwargs):
        if request.method.upper() == "OPTIONS":
            return super().dispatch(request, *args, **kwargs)

        # Set by oauth2_provider.middleware.OAuth2ExtraTokenMiddleware
        if not hasattr(request, "access_token"):
            return HttpResponseForbidden()

        client_id = request.access_token.application.client_id
        if client_id not in self.get_allowed_client_ids():
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)
