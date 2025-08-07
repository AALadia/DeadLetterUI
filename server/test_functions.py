from ApiRequests import ApiRequests
from mongoDb import db
from builderObjects import createUserObject
import pytest
from objects import User
from firebaseObject import firebaseObject, firebaseObject2


def wipeDatabase():
    db.delete({}, 'DeadLetters')
    db.delete({}, 'Users')
    db.delete({}, 'Roles')


def test_deadLetter():
    wipeDatabase()
    user = createUserObject()
    user = db.create(user.model_dump(by_alias=True), 'Users')
    ApiRequests().createDeadLetter('testTopic', {'test': 'value'},
                                   'testTopicName', 'testSubscriber',
                                   'http://127.0.0.1:5000/mockPost',
                                   'Test error message')
    deadLetters = db.read({'_id': 'testTopic'}, 'DeadLetters', findOne=True)
    res = ApiRequests().replayDeadLetter(deadLetterId='testTopic',
                                         userId=user['_id'])
    assert res['_version'] == 2
    assert res['status'] == 'success'


def test_auth():
    try:
        wipeDatabase()
        user = ApiRequests().loginWithGoogle(firebaseObject)
        user = db.read({'_id': user['_id']}, 'Users', findOne=True)
        assert user['_id'] == firebaseObject['uid']
        assert user['email'] == firebaseObject['email']
        assert user['password'] == None
        for x in user['roles']:
            assert x['value'] == True
        # create another user
        user2 = ApiRequests().loginWithGoogle(firebaseObject2)
        user2 = db.read({'_id': user2['_id']}, 'Users', findOne=True)
        assert user2['_id'] == firebaseObject2['uid']
        for x in user2['roles']:
            assert x['value'] == False

    finally:
        wipeDatabase()


def test_create20DeadLetters():
    wipeDatabase()

    ### Create 20 dead letters with different IDs
    for i in range(20):
        ApiRequests().createDeadLetter(id=f'testTopic_{i}',
                                       originalMessage={'test': f'value_{i}'},
                                       topicName='testTopicName',
                                       subscriberName='testSubscriber',
                                       endpoint=f'http://example.com/{i}',
                                       errorMessage=f'Test error message {i}')
    deadLetters = db.read({}, 'DeadLetters')
    assert len(deadLetters) == 20


if __name__ == "__main__":
    test_auth()
    test_deadLetter()
    test_create20DeadLetters()
    print("All tests passed successfully.")
