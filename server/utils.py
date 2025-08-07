import random
import string
from urllib.parse import urlparse


def split_url_and_last_segment(full_url: str) -> tuple[str, str]:
    parsed = urlparse(full_url)
    path = parsed.path

    # Remove trailing slash if any, then split
    path_parts = path.rstrip("/").split("/")

    if not path_parts or path_parts == ['']:
        raise ValueError("URL must have a path with at least one segment.")

    last_segment = path_parts[-1]
    # Reconstruct the path without the last segment
    base_path = "/".join(path_parts[:-1]) + "/"

    # Build the full base URL
    base_url = f"{parsed.scheme}://{parsed.netloc}{'/' if base_path == '/' else '/' + base_path}"
    
    return base_url, last_segment

def generateRandomString():
    return ''.join(
        random.choice(string.ascii_letters + string.digits) for _ in range(32))

def updateData(dataToUpdate, updateQuery, unupdatableKeys):

    def set_nested(data, key, value):
        keys = key.split('.')
        for k in keys[:-1]:
            data = data.setdefault(k, {})
        data[keys[-1]] = value

    for key, value in updateQuery.items():
        if key in unupdatableKeys:
            raise ValueError(f'{key} is not updatable')
        firstKey = key.split('.')[0]
        if firstKey not in dataToUpdate.keys():
            raise ValueError(f'{key} is not a valid parameter')

        # if it has a dot, it means it is a nested object
        if '.' in key:
            set_nested(dataToUpdate, key, value)
        else:
            dataToUpdate[key] = value
    return dataToUpdate