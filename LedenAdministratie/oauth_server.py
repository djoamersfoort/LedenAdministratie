from oauthlib.oauth2.rfc6749.endpoints import TokenEndpoint
from oauthlib.openid.connect.core.endpoints.pre_configured import Server as BaseServer
from oauthlib.openid.connect.core.grant_types import RefreshTokenGrant


class Server(BaseServer):
    def __init__(self, request_validator, *args, **kwargs):
        super().__init__(request_validator, *args, **kwargs)
        self.refresh_grant = RefreshTokenGrant(request_validator)
        TokenEndpoint.__init__(
            self,
            default_grant_type="authorization_code",
            grant_types={
                "authorization_code": self.token_grant_choice,
                "password": self.password_grant,
                "client_credentials": self.credentials_grant,
                "refresh_token": self.refresh_grant,
            },
            default_token_type=self.bearer,
        )
