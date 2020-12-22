from .session import ColonySession
from requests import Session
from urllib.parse import urljoin
from .exceptions import Unauthorized
from .blueprints import BlueprintsManager


class ColonyClient(object):
    """Base class for Colony API access"""
    API_URL = 'api/'

    def __init__(self,
                 colony_host: str = 'https://cloudshellcolony.com',
                 space: str = None,
                 token: str = None,
                 account: str = None,
                 email: str = None,
                 password: str = None,
                 session: ColonySession = ColonySession()):

        self.base_url = urljoin(colony_host, self.API_URL)
        self.session = session
        self.space = space

        if token:
            self.token = token

        elif all([account, email, password]):
            self.token = ColonyClient.login(
                account, email, password, self.session, self.base_url)

        self.session.init_bearer_auth(token)
        # TODO(ddovbii):
        # Remove cyclic dependency. Split client to high-level colony client and low-level
        # transport http client. Then, pass http client instead of self
        self.blueprints = BlueprintsManager(self, self.space)

    def __del__(self):
        if self.session:
            try:
                self.session.close()
            except Exception:
                raise
            finally:
                self.session = None

    @staticmethod
    def login(account: str,
              email: str,
              password: str,
              session: Session = ColonySession(),
              endpoint: str = 'https://cloudshellcolony.com/api'):
        path = urljoin(endpoint, f"accounts/{account}/login")
        payload = {
            'email': email,
            'password': password
        }
        resp = session.post(url=path, json=payload)
        if resp.status_code != 200:
            #TODO(ddovbii): implement exceptions and error handler
            raise Unauthorized("Login Failed")

        return resp.json().get('access_token', '')

    def request(self,
                endpoint: str,
                method: str = "GET",
                params: dict = None,
                headers: dict = None) -> dict:
        """Gets response as Json"""
        if method not in ("GET", "PUT", "POST", "DELETE"):
            raise ValueError("Method must be in [GET, POST, PUT, DELETE]")

        if headers:
            self.session.headers.update(headers)

        if method in ("POST", "PUT", "DELETE"):
            self.session.headers.update({
                'Content-Type': 'application/json'
            })

        if params is None:
            params = {}

        url = urljoin(self.base_url, endpoint)

        response = self.session.request(method=method, url=url, json=params)

        if response.status_code >= 400:
            # TODO(ddovbii): implement exceptions and error handler
            message = ";".join(
                [f"{err['name']}: {err['message']}" for err in response.json().get('errors', [])]
            )
            raise Exception(message)

        return response.json()
