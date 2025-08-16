from pydantic import BaseModel, Field, field_validator,model_validator,computed_field
from typing import Any, Optional, Literal,Self
from roles import UserRoles, RoleSetter, AllRoles
import datetime
from utils import updateData
from pydantic_core import Url
from pubSubPublisherAndSubscriber import publisher,subscriber


class User(BaseModel):
    id: str = Field(..., alias='_id')
    name: str = Field(..., description='Name field')
    email: str | None = Field(None, description='email field')
    password: str | None = Field(None, description='Password field')
    createdAt: datetime.datetime
    roles: UserRoles
    userType: str | None = Field(None, description='User type')
    version: int = Field(1, alias='_version')

    def setRole(self, userType: str) -> dict:
        roleSetter = RoleSetter(userRoles=self.roles)
        if userType == 'superAdmin':
            roleSetter.setSuperAdminRoles()
            self.userType = 'superAdmin'
        else:
            roleSetter.setRole(userType)
            self.userType = userType
        return self

    def setSpecificRole(self, roleId: str, value: bool) -> dict:

        if self.userType == None:
            raise ValueError('User type not set, cannot set role')

        roleSetter = RoleSetter(userRoles=self.roles)
        roleSetter.setSpecificRole(roleId, value)
        return self

    def setUserPassword(self, password: str):
        self.password = password
        return self

    def updateUserData(self, userData: dict, dataToUpdate: dict):
        newUserData = updateData(userData, dataToUpdate, self.id)
        return newUserData

    def isAuthorized(self, roleId: str) -> bool:
        roles = self.roles.getRole(roleId)
        return roles.value

    def checkIfAuthorized(self, roleId: str) -> None:
        roles = self.roles.getRole(roleId)
        if roles.value == False:
            raise ValueError(
                AllRoles().getSpecificRole(roleId).unauthorizedMessage)


class DeadLetter(BaseModel):
    id: str = Field(...,
                    description="Unique ID of the failed message",
                    alias="_id")
    version: int = Field(default=1, alias="_version")
    originalMessage: dict = Field(
        ..., description="The original message payload that failed")
    retryCount: int = Field(default=0,
                            description="Number of retry attempts made")
    status: Literal["pending", "success",
                    "failed"] = Field(default="pending",
                                      description="Current retry status")
    createdAt: datetime.datetime = Field(
        default_factory=datetime.datetime.now(tz=datetime.timezone.utc),
        description="When the dead letter was created")
    lastTriedAt: datetime.datetime | None = Field(
        default=None, description="When it was last retried")
    publisherProjectId: str = Field(None, description="Project ID of the publisher")
    endPoints: list[str] = Field(None, description="Endpoint URL for the subscription")
    errorMessage: str | None = Field(None, description="Error message if retry failed")
    originalTopicPath: str | None = Field(None, description="Original topic path for the message")

    @field_validator('createdAt', mode='before')
    def validate_datetime(cls, value: datetime.datetime) -> datetime.datetime:
        if value.tzinfo is None:
            raise ValueError("Datetime must be timezone-aware")
        return value.astimezone(datetime.timezone.utc)

    @model_validator(mode='after')
    def setPublisherProjectId(self) -> Self:
        split = self.originalTopicPath.split('/')
        self.publisherProjectId = split[1]
        subscriptions = publisher.list_topic_subscriptions(request={"topic": self.originalTopicPath})
        endpoints = []
        for sub in subscriptions:
            sub = subscriber.get_subscription(request={"subscription": sub})
            if sub.push_config and sub.push_config.push_endpoint:
                endpoints.append(sub.push_config.push_endpoint)

        self.endPoints = endpoints
        return self

    def retryMessage(self) -> None:
        self.retryCount += 1
        self.lastTriedAt = datetime.datetime.now(tz=datetime.timezone.utc)

    def markAsSuccess(self) -> None:
        self.status = "success"

    def markAsFailed(self, errorMessage) -> None:
        self.status = "failed"
        self.errorMessage = errorMessage
