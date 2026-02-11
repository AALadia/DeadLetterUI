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
            response.raise_for_status(
            )  # Raises an HTTPError for bad responses
            return response.json()
        except Exception as e:
            tb = traceback.format_exc()
            raise ValueError(f"{str(e)}\nTraceback:\n{tb}")
