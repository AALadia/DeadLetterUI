import requests
import traceback
from urllib.parse import urljoin


class ServerRequest:

    def __init__(self, serverBaseUrl, headers):
        self.serverBaseUrl = serverBaseUrl
        self.headers = headers

    def post(self, path, payload):
        url = urljoin(self.serverBaseUrl, path)
        try:
            response = requests.post(url,
                                     json=payload,
                                     headers=self.headers,
                                     timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            server_tb = str(e)
            try:
                body = response.json()
                # A push handler answers a safe traceback; a refused
                # caller (401) only a message.
                server_tb = (body.get('traceback') or body.get('message')
                             or str(e))
            except Exception:
                pass
            raise ValueError(server_tb)
        except Exception as e:
            raise ValueError(str(e))
