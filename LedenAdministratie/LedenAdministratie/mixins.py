from django.contrib.auth.mixins import UserPassesTestMixin
from django.conf import settings
from .models import APIToken
import requests


class PermissionRequiredMixin(UserPassesTestMixin):
    required_permission = 'LedenAdministratie.view_member'

    def check_user(self, user):
        if user.is_authenticated and user.has_perm(self.required_permission) and user.is_active:
            return True
        return False

    def test_func(self):
        return self.check_user(self.request.user)


class ApiPermissionRequired(UserPassesTestMixin):

    def test_func(self):
        if 'HTTP_AUTHORIZATION' not in self.request.META:
            return False

        token = self.request.META['HTTP_AUTHORIZATION']
        if not token.startswith('IDP '):
            return False

        token = token.split(' ')
        token = token[1]

        # Check the token against IDP
        headers = {'Authorization': 'Bearer {0}'.format(token)}
        response = requests.get(settings.IDP_API_URL, headers=headers)
        if response.ok:
            return True

        return False

class APITokenMixin:

    token_type = 'idp'

    def check_api_token(self):
        token = self.request.POST.get('token', '')
        if token == '':
            return False

        try:
            apitoken = APIToken.objects.get(token_type=self.token_type)
            if apitoken.token == token:
                return True
        except APIToken.DoesNotExist:
            return False

        return False
