from pymongo import MongoClient, ReturnDocument
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, OperationFailure
from AppConfig import AppConfig
import time
import os


class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is not None:
            raise Exception("An instance already exists! Cannot create 2 instances because this leads to bugs")
        cls._instance = super().__new__(cls)
        return cls._instance



class mongoDb():

    def __init__(self, uri=None, databaseName=None, replicaSetEnabled=False):
        """if uri is None, connect to the appropriate uri based on the environment
            if uri is provided, we need the databaseName as well
        """

        # connect to custom uri if provided
        if uri is not None:
            if databaseName is None:
                raise Exception(
                    'Database name is required when custom uri is provided')

            self.client = MongoClient(uri,
                                      server_api=ServerApi('1'),
                                      tz_aware=True)

        # connect to the appropriate uri based on the environment
        elif AppConfig().getEnvironment() == 'cloudprod':
            uri = os.getenv('MONGO_URI')

            if uri is None:
                raise Exception(
                    'MONGO_URI environment variable is not set')

            self.client = MongoClient(uri,
                                      server_api=ServerApi('1'),
                                      tz_aware=True)

        elif AppConfig().getEnvironment() == 'clouddev':
            uri = "mongodb+srv://ladia123:Bigreddog12.@cluster0.pgvpdb1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
            self.client = MongoClient(uri,
                                      server_api=ServerApi('1'),
                                      tz_aware=True)

        # testEnvironment is used for automated testing while the actual is used for production / development
        elif AppConfig().getEnvironment() == 'localdev':
            self.client = MongoClient('localhost', 27017, tz_aware=True)

        elif AppConfig().getEnvironment() == 'localprod':
            self.client = MongoClient('localhost', 27017, tz_aware=True)

        self.databaseName = AppConfig().getDatabaseName() if databaseName is None else databaseName

        self.db = self.client[self.databaseName]

        self.replicaSetEnabled = self.checkReplicaSet()
        

    def ping(self):
        try:
            start_time = time.time()  # get current time
            self.client.admin.command('ping')
            end_time = time.time()  # get current time after ping

            elapsed_time = end_time - start_time  # calculate elapsed time
            elapsed_time_ms = elapsed_time * 1000  # convert to milliseconds

            print(
                "Pinged your deployment. You successfully connected to MongoDB! Response time: %f ms"
                % elapsed_time_ms)
            return elapsed_time_ms
        except Exception as e:
            print(e)

    def create(self, data, collection_name, session=None):
        """Insert a document into the collection and return the created data."""
        print("Creating data in collection: " + collection_name )

        if '_version' not in data:
            raise ValueError("'_version' field is required when creating")

        start_time = time.time()  # get current time
        result = self.db[collection_name].insert_one(data, session=session)
        end_time = time.time()  # get current time after ping

        elapsed_time = end_time - start_time  # calculate elapsed time
        elapsed_time_ms = elapsed_time * 1000  # convert to milliseconds

        print(collection_name + " Response time: %f ms" % elapsed_time_ms)
        return self.db[collection_name].find_one({"_id": result.inserted_id},
                                                 session=session)

    def aggregate(self, pipeline: list, collection_name: str, session=None, findOne=False):
        cursor = self.db[collection_name].aggregate(pipeline, session=session)
        if findOne:
            try:
                return next(cursor, None)
            except StopIteration:
                return None
        return list(cursor)

    def read(self,
             query,
             collection_name,
             projection={},
             session=None,
             findOne=False,
             countOnly=False,
             ):
        """Read documents from the collection."""
        start_time = time.time()  # get current time

        if findOne:
            data = self.db[collection_name].find_one(query,
                                                     projection,
                                                     session=session)

        elif countOnly:
            data = self.db[collection_name].count_documents(query,
                                                           session=session)
        else:
            data = list(self.db[collection_name].find(query,
                                                      projection,
                                                      session=session))
        end_time = time.time()  # get current time after ping

        elapsed_time = end_time - start_time  # calculate elapsed time
        elapsed_time_ms = elapsed_time * 1000  # convert to milliseconds

        print(collection_name + ' ' + str(query) +
              " Response time: %f ms" % elapsed_time_ms)
        return data

    def readWithPagination(self,
                           query,
                           collection_name,
                           page,
                           limit,
                           projection={},
                           sort={
                               'keyToSort': None,
                               'sortOrder': None
                           },
                           reverse=False,
                           session=None):

        # add validations for page and limit
        if limit == None or limit < 1:
            if page > 1:
                raise ValueError(
                    "Page must be 1 if limit is None or less than 1")
        """Read documents from the collection with pagination."""
        start_time = time.time()  # get current time

        # Get the total number of documents matching the query
        totalDocuments = self.db[collection_name].count_documents(query)

        #set limit to total document if limit == None
        if limit is None:
            limit = totalDocuments  # or any sensible large number

        # Create the MongoDB query
        cursor = self.db[collection_name].find(query,
                                               projection,
                                               session=session)

        if reverse:
            cursor = cursor.sort([('$natural', -1)])

        # Apply sorting if keyToSort is provided
        if sort['keyToSort'] and sort['sortOrder'] != 0:
            cursor = cursor.sort(sort['keyToSort'], sort['sortOrder'])

        # Calculate the number of documents to skip
        skip = (page - 1) * limit
        # Apply skip and limit for pagination AFTER sorting
        cursor = cursor.skip(skip).limit(limit)

        # Retrieve the documents
        data = list(cursor)

        # Calculate total pages
        if totalDocuments == 0:
            totalPages = 0
        else:
            totalPages = (totalDocuments + limit - 1) // limit

        end_time = time.time()  # get current time after query

        elapsed_time = end_time - start_time  # calculate elapsed time
        elapsed_time_ms = elapsed_time * 1000  # convert to milliseconds

        print(collection_name + ' ' + str(query) +
              " Response time: %f ms" % elapsed_time_ms)

        # Return the paginated data along with pagination metadata
        return {
            'data': data,
            'page': page,
            'limit': limit,
            'totalDocuments': totalDocuments,
            'totalPages': totalPages
        }

    def getDatabaseName(self):
        """Get the name of the database."""
        return self.databaseName
        

    def update(self,
               query,
               new_values,
               collection_name,
               checkVersion=True,
               incrementVersion=True,
               session=None):
        """Update documents in the collection."""
        print('Updating data in collection: ' + collection_name +
              ' with query: ' + str(query))

        if collection_name not in self.db.list_collection_names():
            raise ValueError('Collection does not exist: ' +
                                collection_name)
        
        if checkVersion:
            latestData = self.db[collection_name].find_one(
                {
                    '_id': query['_id'],
                    '_version': query['_version']
                },
                session=session)
            if latestData is None:
                raise Exception(
                    'Your data is outdated. Please refresh the page and try again.'
                )
        else:
            latestData = self.db[collection_name].find_one(
                {'_id': query['_id']}, session=session)

        newVersion = latestData['_version'] + 1
        oldVersion = newVersion - 1
        new_values['_version'] = newVersion

        # we update the query with the new version
        if checkVersion == True:
            query['_version'] = oldVersion
        else:
            if '_version' in query:
                query.pop('_version')

        def find_instance(d, o, path=""):
            if isinstance(d, dict):
                for key, value in d.items():
                    current_path = f"{path}.{key}" if path else key  # Construct the current path

                    if isinstance(value, dict):
                        # Recursively check nested dictionaries
                        found, instance_path = find_instance(
                            value, o, current_path)
                        if found:
                            print('object detected', instance_path)
                    elif isinstance(value, list):
                        # Recursively check nested lists
                        for i, item in enumerate(value):
                            found, instance_path = find_instance(
                                item, o, f"{current_path}[{i}]")
                            if found:
                                print('object detected', instance_path)
                    elif isinstance(value, o):
                        # Return True and the path if a value is an instance of the specified class
                        print('object detected', current_path)

            elif isinstance(d, list):
                for i, item in enumerate(d):
                    found, instance_path = find_instance(
                        item, o, f"{path}[{i}]")
                    if found:
                        print('object detected', instance_path)

            # Return False and an empty string if no instance of the class is found
            return False, ""

        # from objects import Unit
        # find_instance(new_values, Unit)

        if incrementVersion == False:
            new_values.pop('_version')

        result = self.db[collection_name].update_many(query, {
            '$set': new_values,
        },
                                                      session=session)

        if incrementVersion == True:
            if result.modified_count == 0:
                raise ValueError("No documents were modified.")

        if checkVersion == True:
            query.pop('_version')

        updatedData = self.read(query,
                                collection_name,
                                session=session,
                                findOne=True)
        return updatedData

    def delete(self, query, collection_name, session=None):
        """Delete documents from the collection."""
        print('Deleting data in collection: ' + collection_name +
              ' with query: ' + str(query))

        if query == {} and AppConfig().getIsProductionEnvironment():
            raise Exception(
                'You cannot delete all documents in the collection in production environment'
            )

        deleted_result = self.db[collection_name].delete_many(query,
                                                              session=session)

        if deleted_result.deleted_count > 0:
            return deleted_result.deleted_count
        else:
            return 'No document to delete'

    def getAllCollections(self):
        """Get all collections in the database."""
        return self.db.list_collection_names()

    def deleteAllDataInDatabaseForDevEnvironment(self):
        """Delete all documents from the collection. Only works in the dev environment"""

        if not AppConfig().getIsDevEnvironment():
            raise Exception(
                'This function is only available in the localdev environment')

        allCollections = self.getAllCollections()
        for x in allCollections:
            self.db[x].delete_many({})

    def createTransaction(self, updateFunction):
        if AppConfig().getIsCloudEnvironment() or self.replicaSetEnabled:
            max_retries = 5
            for attempt in range(max_retries):
                with self.client.start_session() as session:
                    try:
                        session.start_transaction()
                        res = updateFunction(session)
                        session.commit_transaction()
                        return res

                    except OperationFailure as e:
                        labels = e.details.get("errorLabels", []) if e.details else []
                        if "TransientTransactionError" in labels and attempt < (max_retries - 1):
                            session.abort_transaction()
                            # exponential back-off (e.g. 0.1, 0.2, 0.4, …)
                            time.sleep(0.1 * (2 ** attempt))
                            continue
                        else:
                            session.abort_transaction()
                            raise

                    except Exception:
                        session.abort_transaction()
                        raise

            raise RuntimeError(f"Transaction failed after {max_retries} attempts.")
        else:
            return updateFunction(None)

    def getAllCollectionNames(self):
        """Get all collections in the database."""
        return self.db.list_collection_names()

    def findOneAndUpdate(self,query,update,collectionName,upsert=True,session=None) -> dict:
        result = self.db[collectionName].find_one_and_update(
            query,              # Filter: find a document with the specified unit.
            update,    # Update: increment the sequence field by 1.
            upsert=upsert,                 # Create the document if it doesn't exist.
            return_document=ReturnDocument.AFTER,
            session=session  # Return the document after applying the update.
        )

        return result

    def checkReplicaSet(self, uri="mongodb://localhost:27017"):
        """
        Connects to the MongoDB instance at the given URI and returns
        True if it’s part of a replica set, False if it’s standalone
        or if the connection/command fails.
        """
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            # "isMaster" (or "hello" on newer servers) reveals replica-set info
            ismaster_info = client.admin.command("isMaster")
        except (ConnectionFailure, OperationFailure) as e:
            # Couldn’t connect or couldn’t run the command → treat as “not a replica set”
            print(f"ERROR: Could not connect or run isMaster: {e}")
            return False

        return "setName" in ismaster_info





class mainDb(mongoDb, Singleton):
    def __init__(self, uri=None, databaseName=None):
        super().__init__(uri, databaseName)

class TestDb(mongoDb, Singleton):
    def __init__(self):
        super().__init__(None, None)

class PubSubMockDb(mongoDb, Singleton):
    def __init__(self, uri=None, databaseName=None):
        super().__init__(uri, databaseName)

db = mainDb('mongodb+srv://cloudRunDeadLetter:2Zgf5clqssM7TLCt@deadletter.hjd3a6i.mongodb.net/?retryWrites=true&w=majority&appName=deadletter','deadletter')
testDb = TestDb()
pubSubMockDb = PubSubMockDb(None,'pubSubMockDb')

if __name__ == '__main__':

    pass

    # # Convert to UTC
    # startDate_utc = startDate_local.astimezone(pytz.utc)
    # endDate_utc = endDate_local.astimezone(pytz.utc)

    # invoiceNumbers = [
    #     {
    #         'startNumber': 6869,
    #         'endNumber': 6900,
    #         'cancelled': [6875, 6876, 6894],
    #         'error': [6881],
    #         'missing': []
    #     },
    #     {
    #         'startNumber': 27201,
    #         'endNumber': 27250,
    #         'cancelled': [],
    #         'error': [],
    #         'missing': []
    #     },
    #     {
    #         'startNumber': 27251,
    #         'endNumber': 27300,
    #         'cancelled': [27258, 27267, 27290, 27295, 27296],
    #         'missing': [27272, 27299]
    #     },
    #     {
    #         'startNumber': 27151,
    #         'endNumber': 27200,
    #         'cancelled': [],
    #         'missing': [27157, 27161]
    #     },
    #     {
    #         'startNumber': 27141,
    #         'endNumber': 27150,
    #         'cancelled': [],
    #         'missing': [27143, 27146]
    #     },
    #     {
    #         'startNumber': 27251,
    #         'endNumber': 27300,
    #         'cancelled': [27258, 27267,27290,27295,27296],
    #         'missing': [27272,27299]
    #     },
    #     {
    #         'startNumber': 6901,
    #         'endNumber': 6938,
    #         'cancelled': [6912,6926,6936],
    #         'missing': [6914]
    #     },
    #     {
    #         'startNumber': 27351,
    #         'endNumber': 27369,
    #         'cancelled': [27354],
    #         'missing': [27357],
    #         'error': [27351]
    #     },
    # ]

    # salesOrdersInvoiceNumbers = [
    #     x['invoiceNumber'] for x in salesOrders if x['invoiceDate'] is not None
    #     and x['invoiceNumber'] is not None and x['invoiceImageList'] is not []
    # ]

    # for invoiceNumber in invoiceNumbers:
    #     startNumber = invoiceNumber['startNumber']
    #     endNumber = invoiceNumber['endNumber']
    #     cancelled = invoiceNumber['cancelled']
    #     missing = invoiceNumber['missing']
    #     for i in range(startNumber, endNumber + 1):
    #         if i in cancelled or i in missing:
    #             continue

    #         if str(i) not in salesOrdersInvoiceNumbers:
    #             print(i)

    # check invoice numbers outside of range
    # ranges = [(x['startNumber'], x['endNumber']) for x in invoiceNumbers]

    # for salesOrder in salesOrders:
    #     if salesOrder['invoiceNumber'] is not None and salesOrder[
    #             'invoiceDate'] is not None:
    #         if salesOrder['invoiceDate'] > startDate_utc and salesOrder[
    #                 'invoiceDate'] < endDate_utc:
    #             inRange = False
    #             for r in ranges:
    #                 if int(salesOrder['invoiceNumber']) >= r[0] and int(
    #                         salesOrder['invoiceNumber']) <= r[1]:
    #                     inRange = True
    #                     break

    #             if not inRange:
    #                 print(salesOrder['invoiceNumber'])

    #____________________________________
