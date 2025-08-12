from types import FunctionType
from .__abstractService import AbstractService, Path
import os
from .__request import request
from .__getIsProductionEnv import getIsProductionEnv
import requests


class WarehouseManagementService(AbstractService):

    def __init__(self, **data):
        super().__init__(**data)
        self.isOnline = self.ping()  # Check if the service is online upon initialization

    def request(self, functionName: str, method: str, data: dict):
        base_url = self.path.prod if getIsProductionEnv() else self.path.dev
        url = base_url + functionName
        return request(url, method, data)

    def ping(self):
        base_url = self.path.prod if getIsProductionEnv() else self.path.dev
        try:
            response = requests.head(base_url, timeout=0.2)
            # If server responds, even with 404/403/etc, it's online
            return True
        except requests.ConnectionError:
            # Server is unreachable
            return False
        except requests.Timeout:
            # Server is not responding in time
            return False
        except requests.RequestException:
            # Catch-all for other request-related issues
            return False


warehouseManagementService = WarehouseManagementService(
    path=Path(prod=os.getenv("warehouseManagementServicePath"),
              dev="http://127.0.0.1:6000/"))

print(warehouseManagementService.model_dump())
