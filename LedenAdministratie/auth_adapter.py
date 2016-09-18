from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse


class AnsFridusSocialAccount(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        u = sociallogin.account.user
        if not u.email.split('@')[1] == "login.scouting.nl":
            raise ImmediateHttpResponse('Scouting logins only!!')
