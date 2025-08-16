from objects import DeadLetter, User
import datetime
from utils import generateRandomString
from roles import AllRoles


def createDeadLetterObject(
    id: str = 'random',
    originalMessage: dict = {'test': 'value'},
    originalTopicPath: str = "projects/starpack-b149d/topics/test",
    status: str = 'failed',
    createdAt: datetime.datetime = datetime.datetime.now(
        tz=datetime.timezone.utc),
    lastTriedAt: datetime.datetime | None = None,
    retryCount:int = 0
) -> DeadLetter:

    if id == 'random':
        id = generateRandomString()

    return DeadLetter(
        _id=id,
        originalMessage=originalMessage,
        retryCount=retryCount,
        status=status,
        createdAt=createdAt,
        lastTriedAt=lastTriedAt,
        originalTopicPath=originalTopicPath,
    )


def createUserObject(_id: str = None,
                     role: str = 'superAdmin',
                     name: str = 'testUserName') -> User:
    if _id is None:
        _id = generateRandomString()

    return User(_id=_id,
                name=name,
                email=name + '@test.com',
                password=name + '123',
                createdAt=datetime.datetime.now(tz=datetime.timezone.utc),
                type=role,
                roles=AllRoles().getAllRoles(),
                _version=0).setRole(role)


if __name__ == "__main__":
    obj = createDeadLetterObject()
