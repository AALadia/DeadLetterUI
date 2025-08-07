from AppConfig import AppConfig
from roles import *
import pytest


def test_Role():
    role = Role(_id="canUpdateUserRole",
                value=False,
                description="can update user role",
                unauthorizedMessage='You are not authorized to update user role',
                collectionsTransacted=["Users"])
    role.switchRole()
    assert role.value == True
    role.switchRole()
    assert role.value == False
    role.setTrue()
    assert role.value == True
    role.setFalse()
    assert role.value == False


def test_RoleTracker():
    # test validate if all roles were transacted returns true
    roleTracker = RoleTracker()
    for role in AllRoles().getAllRoles():
        roleTracker.addRole(role)
    assert roleTracker.validateIfAllRolesWereTransacted() == True

    # test validate if all roles were transacted raises ValueError
    roleTracker2 = RoleTracker()
    missing1Role = AllRoles().getAllRoles()[:-1]
    for role in missing1Role:
        roleTracker2.addRole(role)
    with pytest.raises(ValueError):
        roleTracker2.validateIfAllRolesWereTransacted()


def test_RoleSetter():
    userRoles = UserRoles(AllRoles().getAllRoles())
    for x in userRoles.getRoles():
        assert x.value == False

    RoleSetter(userRoles=userRoles).setSuperAdminRoles()

    for x in userRoles.getRoles():
        assert x.value == True


if __name__ == '__main__':
    if AppConfig().getIsProductionEnvironment():
        raise ValueError('Not to be run in production environment')
    test_Role()
    test_RoleTracker()
    test_RoleSetter()
