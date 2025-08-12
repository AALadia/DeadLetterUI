from pydantic import BaseModel, Field, HttpUrl, field_validator
import inspect
import os
from abc import ABC, abstractmethod
from typing import Optional


def get_initializer_filename():
    # Walk through the stack to find where this class was instantiated
    current_file = os.path.abspath(__file__)
    for frame_info in inspect.stack():
        frame = frame_info.frame
        filename = os.path.abspath(frame_info.filename)
        if filename != current_file:
            return os.path.splitext(
                os.path.basename(filename)
            )[0]  # Return the filename of the first frame that isn't this file
    return None


class Path(BaseModel):
    prod: str | None
    dev: str | None

    @staticmethod
    def __sharedValidation(v):
        if v == None:
            return v
        if not isinstance(v, str):
            raise ValueError("Path must be a string")
        if not v.endswith("/"):
            raise ValueError("Path must end with a '/'")
        if not v.startswith("http"):
            raise ValueError("Path must be a valid URL starting with http:// or https://")
        return v

    @field_validator("prod", mode="before")
    @classmethod
    def validate_prod(cls, v):
        return cls.__sharedValidation(v)

    @field_validator("dev", mode="before")
    @classmethod
    def validate_dev(cls, v):
        return cls.__sharedValidation(v)


class AbstractService(BaseModel, ABC):
    path: Path
    name: Optional[str] = None
    isOnline: bool = Field(default=False, description="Indicates if the service is online")

    def __init__(self, **data):
        # Set name only if not explicitly provided
        if 'name' not in data or data['name'] is None:
            data['name'] = get_initializer_filename()
        super().__init__(**data)

    @abstractmethod
    def request(self):
        pass

    @abstractmethod
    def ping(self):
        """Ping the service to check if it's available."""
        pass


if __name__ == "__main__":
    service = AbstractService(
        path=Path(prod="https://prod.example", dev="https://dev.example"))
    print(service.model_dump())
