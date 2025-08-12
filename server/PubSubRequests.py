from route_config import route_config
from pubSub import PubSub
from ApiRequests import ApiRequests


class Sample():

    @route_config(httpMethod='POST',
                  jwtRequired=False,
                  successMessage='Order created successfully',
                  roleAccess='test')
    def createMessageFromPubSub(self, order: dict):
        message = data['message']
        data = message['data']
        data = PubSub().decodeMessage(data)
        ApiRequests().createDeadLetter(data['_id'],data,'12345','4212',)
        


class PubSubRequests(Sample):

    def __init__(self):
        Sample.__init__(self)
