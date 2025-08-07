from route_config import route_config


class Sample():

    @route_config(httpMethod='POST',
                  jwtRequired=False,
                  successMessage='Order created successfully',
                  roleAccess='test')
    def createAccountingInventoryOrder(self, order: dict):
        pass


class PubSubRequests(Sample):

    def __init__(self):
        Sample.__init__(self)
