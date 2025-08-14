from pydantic import BaseModel, Field, RootModel
from typing import List, Optional


class Role(BaseModel):
    id: str = Field(..., description='Role id', alias='_id')
    value: bool = Field(..., description='Role value')
    description: str = Field(..., description='Role description')
    collectionsTransacted: Optional[List[str]] = Field(
        default=[],
        description='List of collections transacted by role',
        exclude=True)
    unauthorizedMessage: Optional[str] = Field(
        default='',
        description=
        'Message to show when user is unauthorized to perform this role action',
        exclude=True)

    def switchRole(self):
        self.value = not self.value

    def setTrue(self):
        self.value = True

    def setFalse(self):
        self.value = False


class AllRoles(BaseModel):
    roles: List[Role] = Field([
        Role(
            _id="canUpdateUserRole",
            value=False,
            description="can update user role",
            collectionsTransacted=["Users"],
            unauthorizedMessage="You are not authorized to update user roles"),
        Role(
            _id="canReplayDeadLetter",
            value=False,
            description="can replay dead letter",
            collectionsTransacted=["DeadLetters"],
            unauthorizedMessage="You are not authorized to replay dead letters"),
        Role(
            _id="canReceiveNewDeadLetterEmails",
            value=False,
            description="can receive newly created dead letter emails",
            collectionsTransacted=["DeadLetters"],
            unauthorizedMessage="You are not authorized to receive newly created dead letter emails"
        )
    ], )

    def getAllRoles(self) -> List[Role]:
        return self.roles

    def getAllRoleIds(self) -> List[str]:
        return [role.id for role in self.roles]

    def getSpecificRole(self, roleId: str) -> Role:
        for role in self.roles:
            if role.id == roleId:
                return role
        raise ValueError(f'Role {roleId} not found')

    def getRoleCount(self) -> int:
        return len(self.roles)


class UserRoles(RootModel[List[Role]]):

    def getRoles(self):
        return self.root

    def getRole(self, roleId: str):
        for role in self.root:
            if role.id == roleId:
                return role
        raise ValueError(f'Role {roleId} not found')


class RoleTracker(BaseModel):
    ''' This class is used to trach the roles that were set by the role setter and validate if all roles were used'''
    listOfRolesTransacted: List[Role] = Field(default_factory=list,
                                              description='List of roles')

    def addRole(self, role: Role):
        if role in self.listOfRolesTransacted:
            raise ValueError(f'{role.id} has already been transacted')
        else:
            self.listOfRolesTransacted.append(role)

    def validateIfAllRolesWereTransacted(self):
        transacted_ids = {x.id
                          for x in self.listOfRolesTransacted
                          }  # Use a set to avoid duplicates
        allRoles = AllRoles()
        required_ids = set(allRoles.getAllRoleIds())

        if transacted_ids == required_ids:
            return True
        else:
            raise ValueError(
                f'Not all roles were transacted. Only {len(transacted_ids)} out of {allRoles.getRoleCount()} roles were transacted'
            )


class UserRoleTypes():

    def __init__(self):
        self.userTypesRoles = {
            'operator': {
                'canUpdateUserRole': False,
                'canCreateUser': False,
                'canPrintSticker': True,
                'canFragileCheck': False,
                'canQualityCheck': False,
                'canInInventory': False,
                'canCreateUnit': False,
                'canUpdateUnit': False,
                'canCreateOrder': False,
                'canAddOrderNote': False,
                'canReviseOrder': False,
                'canScanOutUnits': False,
                'canCloseOrder': False,
                'canCreateMachine': False,
                'canReturnInventory': False,
                'canViewInventory': False,
                'canUpdateSettings': False,
                'canCreateDelivery': False,
                'canDeleteOrder': False
            },
            'gatherer': {
                'canUpdateUserRole': False,
                'canCreateUser': False,
                'canPrintSticker': True,
                'canFragileCheck': False,
                'canQualityCheck': False,
                'canInInventory': False,
                'canCreateUnit': False,
                'canUpdateUnit': False,
                'canCreateOrder': False,
                'canAddOrderNote': False,
                'canReviseOrder': False,
                'canScanOutUnits': False,
                'canCloseOrder': False,
                'canCreateMachine': False,
                'canReturnInventory': False,
                'canViewInventory': False,
                'canUpdateSettings': False,
                'canCreateDelivery': False,
                'canDeleteOrder': False
            },
            'qualityChecker': {
                'canUpdateUserRole': False,
                'canCreateUser': False,
                'canPrintSticker': False,
                'canFragileCheck': True,
                'canQualityCheck': True,
                'canInInventory': False,
                'canCreateUnit': False,
                'canUpdateUnit': False,
                'canCreateOrder': False,
                'canAddOrderNote': False,
                'canReviseOrder': False,
                'canScanOutUnits': False,
                'canCloseOrder': False,
                'canCreateMachine': False,
                'canReturnInventory': False,
                'canViewInventory': False,
                'canUpdateSettings': False,
                'canCreateDelivery': False,
                'canDeleteOrder': False
            },
            'warehouseMan': {
                'canUpdateUserRole': False,
                'canCreateUser': False,
                'canPrintSticker': False,
                'canFragileCheck': False,
                'canQualityCheck': False,
                'canInInventory': True,
                'canCreateUnit': True,
                'canUpdateUnit': True,
                'canCreateOrder': True,
                'canAddOrderNote': True,
                'canReviseOrder': True,
                'canScanOutUnits': True,
                'canCloseOrder': True,
                'canCreateMachine': False,
                'canReturnInventory': True,
                'canViewInventory': True,
                'canUpdateSettings': False,
                'canCreateDelivery': True,
                'canDeleteOrder': False
            }
        }

    def getConfig(self, userType: str):
        if userType not in self.userTypesRoles:
            raise ValueError(f'User type {userType} not found')
        return self.userTypesRoles[userType]

    def getUserTypes(self):
        userTypes = []
        for key, value in self.userTypesRoles.items():
            userTypes.append(key)

        return userTypes


class RoleSetter(BaseModel):
    userRoles: UserRoles = Field(..., description='User roles')

    def __setRole(self, role: Role, roleId, value: bool,
                  roleTracker: RoleTracker):
        if roleId == role.id:
            roleTracker.addRole(role)  # add role to tracker
            if value == True:
                role.setTrue()
            else:
                role.setFalse()

    def setSuperAdminRoles(self):
        """ Set all roles to true """
        for role in self.userRoles.root:
            role.setTrue()

    def setRole(self, userType: str):
        """ Set a specific role to true or false """

        if userType not in UserRoleTypes().getUserTypes():
            raise ValueError(f'User type {userType} not found')

        roleTracker = RoleTracker()
        for role in self.userRoles.root:
            for key, value in UserRoleTypes().getConfig(userType).items():
                self.__setRole(role, key, value, roleTracker)
        roleTracker.validateIfAllRolesWereTransacted()

    def setSpecificRole(self, roleId: str, value: bool):
        roleTracker = RoleTracker()
        for role in self.userRoles.root:
            self.__setRole(role, roleId, value, roleTracker)
        return self.userRoles.root


if __name__ == "__main__":
    allRoles = AllRoles().getAllRoles()
    userRoles = UserRoles(allRoles)
    superAdmin = RoleSetter(userRoles=userRoles).setSuperAdminRoles()
    print(allRoles)
    print(userRoles.model_dump())
    print(userRoles.model_dump())
    # print(SpecificRoles().getUserTypes())
