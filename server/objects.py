from pydantic import BaseModel, Field, field_validator
from typing import Any, Optional, Literal
from roles import UserRoles, RoleSetter, AllRoles
import datetime
from utils import updateData
from pydantic_core import Url


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
    topicName: str = Field(
        ..., description="Name of the topic the message was received from")
    subscriberName: str = Field(
        ..., description="Name of the subscriber or service that failed")
    endpoint: str = Field(
        ..., description="The endpoint that failed to process the message")
    errorMessage: str = Field(..., description="Error that caused the failure")
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

    @field_validator('createdAt', mode='before')
    def validate_datetime(cls, value: datetime.datetime) -> datetime.datetime:
        if value.tzinfo is None:
            raise ValueError("Datetime must be timezone-aware")
        return value.astimezone(datetime.timezone.utc)

    # @field_validator('endpoint', mode='before')
    # def validate_url(cls, v: str) -> str:
    #     try:
    #         Url(v)  # validate only
    #     except:
    #         raise ValueError("Endpoint must be a valid URL")
    #     return v

    def retryMessage(self) -> None:
        self.retryCount += 1
        self.lastTriedAt = datetime.datetime.now(tz=datetime.timezone.utc)

    def markAsSuccess(self) -> None:
        self.status = "success"

    def markAsFailed(self, errorMessage) -> None:
        self.status = "failed"
        self.errorMessage = errorMessage
