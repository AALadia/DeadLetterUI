from objectGeneratorForTesting import createUserObject
from mongoDb import db
from pubSub import mockDataConsumer
from PubSubRequests import PubSubRequests
from AppConfig import AppConfig


def wipeDatabase():
    if AppConfig().getIsProductionEnvironment():
        raise ValueError('Not to be run in production environment')

    db.delete({}, 'StickersPrinted')
    db.delete({}, 'SequenceTracker')
    db.delete({}, 'ServedOrders')
    db.delete({}, 'UnservedOrders')
    db.delete({}, 'Users')
    db.delete({}, 'Units')
    db.delete({}, 'FirstVerified')
    db.delete({}, 'CurrentInventory')
    db.delete({}, 'OutInventory')
    db.delete({}, 'Settings')
    db.delete({}, 'Machines')


def test_pubSub_accountingToInventory():
    try:
        user = createUserObject()
        user = db.create(user.model_dump(by_alias=True), 'Users')

        consumed = mockDataConsumer.consumeMockData(
            'accounting',
            PubSubRequests().createUnit_accounting, 0)

        unit = db.read({'_id': consumed['message']['_id']},
                       'Units',
                       findOne=True)
        assert unit is not None

        consumed = mockDataConsumer.consumeMockData(
            'accounting',
            PubSubRequests().createUnit_accounting, 1)

        unit = db.read({'_id': consumed['message']['_id']},
                       'Units',
                       findOne=True)
        assert unit is not None

        consumed = mockDataConsumer.consumeMockData(
            'accounting',
            PubSubRequests().createUnit_accounting, 2)

        unit = db.read({'_id': consumed['message']['_id']},
                       'Units',
                       findOne=True)
        assert unit is not None

        consumed = mockDataConsumer.consumeMockData(
            'accounting',
            PubSubRequests().createAndConvertItemAsPack_accounting, 3)

        message = consumed['message']
        packUnit = message['packData']
        boxUnit = message['boxData']
        packUnit = db.read({'_id': packUnit['_id']}, 'Units', findOne=True)
        boxUnit = db.read({'_id': boxUnit['_id']}, 'Units', findOne=True)
        assert packUnit
        assert boxUnit
        assert packUnit['boxProductId'] == boxUnit['_id']
        assert boxUnit['packProductId'] == packUnit['_id']

        consumed = mockDataConsumer.consumeMockData(
            'accounting',
            PubSubRequests().createUnit_accounting, 4)

        unit = db.read({'_id': consumed['message']['_id']},
                       'Units',
                       findOne=True)
        assert unit is not None

        consumed = mockDataConsumer.consumeMockData(
            'accounting',
            PubSubRequests().updateUnitChildOrParent_accounting, 5)

        message = consumed['message']
        child = message['child']
        parent = message['parent']
        child = db.read({'_id': child['_id']}, 'Units', findOne=True)
        parent = db.read({'_id': parent['_id']}, 'Units', findOne=True)
        assert child['boxProductId'] == parent['_id']
        assert parent['packProductId'] == child['_id']

        consumed = mockDataConsumer.consumeMockData(
            'accounting',
            PubSubRequests().createSalesOrder_accounting, 6)

        order = db.read({'_id': consumed['message']['_id']},
                        'UnservedOrders',
                        findOne=True)
        assert order is not None
        messageItemOrderList = consumed['message']['itemsOrderList']
        assert len(messageItemOrderList) == 2
        for item in messageItemOrderList:
            unit = db.read({'_id': item['unit']['_id']}, 'Units', findOne=True)
            assert unit is not None
            unitReservedOrders = unit['reservedOrders']
            assert len(unitReservedOrders) == 1
            assert unitReservedOrders[0]['orderId'] == consumed['message'][
                '_id']
            assert unitReservedOrders[0]['quantity'] == item['quantity']

        consumed = mockDataConsumer.consumeMockData(
            'accounting',
            PubSubRequests().reviseSalesOrder_accounting, 7)

        salesOrder = db.read({'_id': consumed['message']['_id']},
                             'UnservedOrders',
                             findOne=True)

        assert salesOrder is not None

        for x in consumed['message']['itemsOrderList']:
            unit = db.read({'_id': x['unit']['_id']}, 'Units', findOne=True)
            assert unit is not None
            assert x['quantity'] == unit['reservedOrders'][0]['quantity']

        for x in salesOrder['itemsOrderList']:
            unit = db.read({'_id': x['unit']['_id']}, 'Units', findOne=True)
            assert unit is not None
            assert x['quantity'] == [
                y for y in consumed['message']['itemsOrderList']
                if y['unit']['_id'] == x['unit']['_id']
            ][0]['quantity']

        consumed = mockDataConsumer.consumeMockData(
            'accounting',
            PubSubRequests().deleteSalesOrder_accounting, 8)
        res = consumed['res']
        message = consumed['message']

        for x in message['itemsOrderList']:
            unit = db.read({'_id': x['unit']['_id']}, 'Units', findOne=True)
            assert unit['reservedOrders'] == []

        consumed = mockDataConsumer.consumeMockData(
            'accounting',
            PubSubRequests().updateUnit_accounting, 9)


      
        message = consumed['message']
        response = consumed['res']

        updatedUnit = db.read({'_id': response['_id']}, 'Units', findOne=True)

        accountingItemName = message['item']['name']
        accountingItemPacksePerBox = message['item']['packsPerBox']
        accountingItemPieces = message['item']['pieces']
        accountingItemPiecesPerPack = message['item']['piecesPerPack']
        accountingItemColor = message['item']['color']
        accountingItemBrand = message['item']['brand']
        accountingItemPackImage = message['item']['imageList']['packImage']
        accountingItemBoxImage = message['item']['imageList']['boxImage']
        accountingItemProductImage = message['item']['imageList'][
            'productImage']
        accountingItemWeight = message['item']['weight']
        accountingItemIsFragile = message['item']['isFragile']
        accountingItemIsManufactured = message['item']['isManufactured']

        assert updatedUnit['name'] == accountingItemName
        assert updatedUnit['pieces'] == accountingItemPieces
        assert updatedUnit['packsPerBox'] == accountingItemPacksePerBox
        assert updatedUnit['piecesPerPack'] == accountingItemPiecesPerPack
        assert updatedUnit['color'] == accountingItemColor
        assert updatedUnit['brand'] == accountingItemBrand
        assert updatedUnit['imageList']['packImage'] == accountingItemPackImage
        assert updatedUnit['imageList']['boxImage'] == accountingItemBoxImage
        assert updatedUnit['imageList'][
            'productImage'] == accountingItemProductImage
        assert updatedUnit['weight'] == accountingItemWeight
        assert updatedUnit['isFragile'] == accountingItemIsFragile
        assert updatedUnit['isManufactured'] == accountingItemIsManufactured
    finally:
        wipeDatabase()

    # assert mockDataID in unservedOrders


if __name__ == '__main__':
    test_pubSub_accountingToInventory()
    print("Test completed successfully.")
