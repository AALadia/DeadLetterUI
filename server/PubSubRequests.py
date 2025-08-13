from route_config import route_config
from builderObjects import createDeadLetterObject
from mongoDb import db
class DeadLetterActions():

    @route_config(httpMethod='POST',
                  jwtRequired=False,
                  successMessage='Dead letter message created successfully')
    def createDeadLetter(self, _id: str, originalMessage: dict, topicName: str,
                         subscriberName: str, endpoint: str,
                         errorMessage: str) -> dict:

        # idempotency check
        if db.read({'_id': _id}, 'DeadLetters', findOne=True):
            return 'data already exists'

        deadLetterObject = createDeadLetterObject(
            id=_id,
            originalMessage=originalMessage,
            topicName=topicName,
            subscriberName=subscriberName,
            endpoint=endpoint,
            errorMessage=errorMessage)
        res = db.create(deadLetterObject.model_dump(by_alias=True),
                        'DeadLetters')
        return res


class PubSubRequests(DeadLetterActions):

    def __init__(self):
        DeadLetterActions.__init__(self)
