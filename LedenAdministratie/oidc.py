from oauth2_provider.oauth2_validators import OAuth2Validator


# pylint: disable=abstract-method
class DJOOAuth2Validator(OAuth2Validator):
    # Mapping of claim -> required scope
    oidc_claim_scope = {
        "sub": "openid",
        "account_type": "user/basic",
        "stripcard": "user/basic",
        "days": "user/basic",
        "given_name": "user/names",
        "family_name": "user/names",
        "email": "user/email",
        "aanmelden": "aanmelden",
        "media": "media",
    }

    # This needs to be without the 'request' parameter + lambda's to support claim discovery
    # pylint: disable=arguments-differ
    def get_additional_claims(self):
        return {
            "given_name": lambda request: request.user.first_name,
            "family_name": lambda request: request.user.last_name,
            "email": lambda request: request.user.email,
            "aanmelden": lambda request: True,
            "media": lambda request: True,
            "account_type": lambda request: request.user.member.idp_types(),
            "days": lambda request: request.user.member.days,
            "stripcard": lambda request: {
                "count": request.user.member.active_stripcard.count,
                "used": request.user.member.active_stripcard.used,
            }
            if request.user.member.active_stripcard
            else None,
        }
