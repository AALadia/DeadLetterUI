from pydantic import BaseModel, Field, model_validator
import datetime
from typing import List
from roles import *
from mongoDb import db
from objects import User

class AuthHandlerEmailAndPassword(BaseModel):
    email: str
    password: str

    # from objects import User

    def __checkIfUserExists(self, email: str) -> dict:
        user = db.read({'email': email}, 'Users', findOne=True)
        if user == None:
            raise ValueError(
                'Cannot sign up with email and password. Please use google login instead'
            )
        if user['password'] == None:
            raise ValueError(
                'Cannot sign in without password registered. Please use google login instead'
            )
        return user

    def __checkIfPasswordMatchesUser(self, user, password):
        if user['password'] == password:
            return True
        else:
            return False

    def emailAndPasswordFlow(self) -> dict:
        from objects import User
        user = self.__checkIfUserExists(self.email)

        if self.__checkIfPasswordMatchesUser(user, self.password):
            return User(**user)
        else:
            raise ValueError('Password is incorrect')


class AuthHandlerGoogle(BaseModel):
    firebaseUserObject: dict
    email: str = Field(default=None)
    firebaseUserId: str = Field(default=None)
    displayName: str = Field(default=None)

    # from objects import User

    @model_validator(mode='after')
    def set_firebase_id(self) -> "AuthHandlerGoogle":
        self.firebaseUserId = self.firebaseUserObject.get('uid', None)
        return self

    @model_validator(mode='after')
    def set_email(self) -> "AuthHandlerGoogle":
        self.email = self.firebaseUserObject.get('email', None)
        return self

    @model_validator(mode='after')
    def set_display_name(self) -> "AuthHandlerGoogle":
        self.displayName = self.firebaseUserObject.get('displayName', None)
        return self

    def __doesUserIdExist(self, firebaseUserId: str) -> dict:
        user = db.read({'_id': firebaseUserId}, 'Users', findOne=True)
        return user

    def __firstUserExists(self):
        users = db.read({}, 'Users')
        if len(users) > 0:
            return True
        else:
            return False

    def googleLoginFlow(self) -> User:
        from objects import User
        user = self.__doesUserIdExist(self.firebaseUserId)
        if user != None:
            return User(**user)
            #login
        else:
            if self.__firstUserExists():
                user = User(_id=self.firebaseUserId,
                            name=self.displayName,
                            email=self.email,
                            password=None,
                            createdAt=datetime.datetime.now(),
                            roles=UserRoles(AllRoles().getAllRoles()),
                            _version=0)
                return user
            else:
                user = User(_id=self.firebaseUserId,
                            name=self.displayName,
                            email=self.email,
                            password=None,
                            createdAt=datetime.datetime.now(),
                            roles=UserRoles(AllRoles().getAllRoles()),
                            _version=0)
                return user.setRole('superAdmin')
