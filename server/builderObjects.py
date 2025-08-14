from objects import DeadLetter, User
import datetime
from utils import generateRandomString
from roles import AllRoles


def createDeadLetterObject(
        id: str = 'random',
        originalMessage: dict = {'test': 'value'},
        topicName: str = 'testTopic',
        subscriberName: str = 'testSubscriber',
        endpoint: str = 'http://example.com',
        errorMessage: str = 'Test error message',
        status: str = 'failed',
        createdAt: datetime.datetime = datetime.datetime.now(tz=datetime.timezone.utc),
        lastTriedAt: datetime.datetime | None = None,
        publisherProjectId: str = 'testProjectId',
        publisherProjectName: str = 'testPublisherProjectName') -> DeadLetter:

    if id == 'random':
        id = generateRandomString()

    return DeadLetter(_id=id,
                      originalMessage=originalMessage,
                      topicName=topicName,
                      subscriberName=subscriberName,
                      endpoint=endpoint,
                      errorMessage=errorMessage,
                      status=status,
                      createdAt=createdAt,
                      lastTriedAt=lastTriedAt,
                      publisherProjectId=publisherProjectId,
                      publisherProjectName=publisherProjectName)

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
