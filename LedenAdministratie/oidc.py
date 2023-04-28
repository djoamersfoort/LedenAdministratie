from oauth2_provider.oauth2_validators import OAuth2Validator


class DJOOAuth2Validator(OAuth2Validator):

    # Mapping of claim -> required scope
    oidc_claim_scope = {
        "sub": "openid",
        "given_name": "user/names",
        "family_name": "user/names",
        "email": "user/email",
    }

    # This needs to be without the 'request' parameter + lambda's to support claim discovery
    def get_additional_claims(self):
        return {
            "given_name": lambda request: request.user.first_name,
            "family_name": lambda request: request.user.last_name,
            "email": lambda request: request.user.email,
        }
