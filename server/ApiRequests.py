from typing import List
import datetime
from mongoDb import db
from route_config import route_config
from utils import generateRandomString
from objects import User, DeadLetter
from builderObjects import createDeadLetterObject
from functions import retryMessage
from AppConfig import AppConfig



class AuthActions():

    @route_config(httpMethod='POST',
                  jwtRequired=False,
                  createAccessToken=True,
                  successMessage='Login successful')
    def loginWithGoogle(self, firebaseUserObject: dict) -> User:
        from AuthHandler import AuthHandlerGoogle
        user = AuthHandlerGoogle(
            firebaseUserObject=firebaseUserObject).googleLoginFlow()
        userExists = db.read({'_id': user.id}, 'Users', findOne=True)
        if userExists == None:
            user = db.create(user.model_dump(by_alias=True), 'Users')
            user = User(**user)
        return user.model_dump(by_alias=True)


class UserActions():

    @route_config(httpMethod='POST',
                  jwtRequired=True,
                  successMessage='User role updated successfully',
                  roleAccess='canUpdateUserRole')
    def setUserRole(self, userIdToChangeRole: str, userType: str,
                    userId: str) -> User:

        userToChange = db.read({'_id': userIdToChangeRole},
                               'Users',
                               findOne=True)
        userToChange = User(**userToChange)
        userToChange.setRole(userType)

        user = db.update(
            {
                '_id': userToChange.id,
                '_version': userToChange.version
            }, userToChange.model_dump(by_alias=True), 'Users')

        return user

    @route_config(httpMethod='POST',
                  jwtRequired=True,
                  successMessage='User role updated successfully',
                  roleAccess='canUpdateUserRole')
    def setSpecificRoles(self, userIdToChangeRole: str, roleId: str,
                         value: bool, userId: str) -> User:

        userToChange = db.read({'_id': userIdToChangeRole},
                               'Users',
                               findOne=True)
        userToChange = User(**userToChange)
        userToChange.setSpecificRole(roleId, value)

        user = db.update(
            {
                '_id': userToChange.id,
                '_version': userToChange.version
            }, userToChange.model_dump(by_alias=True), 'Users')

        return user

    def __fetchUsers(self,
                     userType: str = None,
                     projection: dict = None) -> List[User]:
        if userType == None:
            users = db.read({}, 'Users', projection=projection)
        else:
            users = db.read({'userType': userType},
                            'Users',
                            projection=projection)

        return users

    @route_config(httpMethod='POST',
                  jwtRequired=True,
                  successMessage='User list fetched successfully')
    def fetchUserList(self, projection: dict = None) -> List[User]:
        users = self.__fetchUsers(projection=projection)
        return users


class DeadLetterActions():
    @route_config(httpMethod='POST',
                  jwtRequired=True,
                  successMessage='Dead letter message updated successfully',
                  roleAccess='canReplayDeadLetter')
    def replayDeadLetter(self, deadLetterId: str, userId: str) -> dict:
        deadLetter = db.read({'_id': deadLetterId},
                             'DeadLetters',
                             findOne=True)
        deadLetter = DeadLetter(**deadLetter)
        deadLetter = retryMessage(deadLetter)
        deadLetter = db.update(
            {
                '_id': deadLetter.id,
                '_version': deadLetter.version
            }, deadLetter.model_dump(by_alias=True), 'DeadLetters')
        return deadLetter

    @route_config(httpMethod='POST',
                  jwtRequired=True,
                  successMessage='Dead letters fetched successfully')
    def listDeadLetters(self,
                        
                        projection: dict | None = None) -> List[DeadLetter]:
        """Fetch a list of dead letters with optional filter and projection."""
        
        deadLetters = db.read({'status':'failed'}, 'DeadLetters', projection=projection)
        return deadLetters


class MockServerForTesting():

    @route_config(httpMethod='POST',
                  jwtRequired=False,
                  successMessage='Mock server response created successfully')
    def mockPost(self, message: dict) -> dict:
        if isinstance(message, dict):
            return {'status': 'success', 'message': message}
        else:
            raise ValueError("Message must be a dictionary")


class ApiRequests(UserActions, DeadLetterActions, AuthActions,
                  MockServerForTesting):

    def __init__(self):
        UserActions.__init__(self)
        DeadLetterActions.__init__(self)
        MockServerForTesting.__init__(self)
        AuthActions.__init__(self)


if __name__ == '__main__':
    # print(AuthActions.loginWithEmailAndPassword.httpMethod)
    # print(AuthActions.loginWithEmailAndPassword.jwtRequired)
    # print(AuthActions.loginWithGoogle.createAccessToken)
    # api = ApiRequests()
    # print(api.loginWithEmailAndPassword.createAccessToken)

    api = ApiRequests()
    # unit = db.read({'_id': 'unit1'}, 'Units', findOne=True)
    # entry = EntryUnit(quantity=10, unit=Unit(**unit))
    # order = {
    #     '_id': 'testOrder1',
    #     'itemOrderList':ItemOrderList([entry]),
    #     'customerName':'Test Customer',
    #     'deliveryDate':datetime.datetime.now(),
    #     'notesList':['Note 1', 'Note 2']
    # }

    # userId = db.read({'name': 'Superadmin'}, 'Users')
    # order = api.createSalesOrder(order=mockOrderFromSales1,
    #                              userId=userId[0]['_id'])
    # print(order)
