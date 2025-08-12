import requests
import json


def request(url: str, method: str, data: dict):
    response = requests.request(method.upper(), url, data=json.dumps(data, default=str),headers={"Content-Type": "application/json"})  # Serialize with fallback
    response.raise_for_status()
    return response.json()