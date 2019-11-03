from django.contrib.auth.mixins import UserPassesTestMixin
from django.conf import settings
from django.utils import timezone
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

        token = token.strip().split(' ')
        token = token[1]

        # Delete all expired session tokens
        APIToken.objects.filter(expires__lt=timezone.now(), token_type='session').delete()

        # Check if token is in the cache
        try:
            APIToken.objects.get(token_type='session', token=token)
            return True
        except APIToken.DoesNotExist:
            # Cached token not found, check the token against IDP
            headers = {'Authorization': 'Bearer {0}'.format(token)}
            response = requests.get(settings.IDP_API_URL, headers=headers)
            if response.ok:
                # Cache the token for 24 hours
                cached_token = APIToken()
                cached_token.token = token
                cached_token.expires = timezone.now() + timezone.timedelta(hours=24)
                cached_token.token_type = 'session'
                cached_token.save()
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
