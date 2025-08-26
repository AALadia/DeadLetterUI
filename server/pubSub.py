from google.cloud import pubsub_v1
from google.oauth2 import service_account
from AppConfig import AppConfig
import os
import datetime
import json
import base64
from mongoDb import pubSubMockDb, PubSubMockDb
from AppConfig import AppConfig
import inspect
from utils import generateRandomString
import functools
from services.__abstractService import AbstractService
from typing import Callable, List
from pydantic import BaseModel, Field, field_validator, field_serializer
import base64
import datetime
from typing import Dict, Optional
import google.auth


def _get_caller_name() -> str:
    # inspect.stack()[0] is this function,
    # [1] is Pydantic internals, so [2] is your caller.
    return inspect.stack()[3].function


def _getIndex():
    data = pubSubMockDb.read({}, AppConfig().projectName)
    return len(data)


class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is not None:
            raise Exception(
                "An instance already exists! Cannot create 2 instances because this leads to bugs"
            )
        cls._instance = super().__new__(cls)
        return cls._instance


class MockData(BaseModel):
    id: str = Field(default_factory=generateRandomString,
                    alias='_id',
                    description='Unique identifier for the mock data')
    version: int = Field(default=1,
                         description='Version of the mock data',
                         alias='_version')
    data: dict = Field(..., description='Mock data to be stored')
    dateOfCreation: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description='Date of creation of the mock data')
    consumeFunctionName: str = Field(
        ..., description='Function name that will consume this data')
    createdByFunctionName: str = Field(
        default_factory=_get_caller_name,
        description='Function name that created this mock data')
    projectName: str = Field(
        default=AppConfig().projectName,
        description='Project name where the mockData is from')
    projectNameConsumers: list[str] = Field(
        ...,
        description='Project names where the mockData will be consumed from')
    index: int = Field(
        default_factory=_getIndex,
        description=
        'count of the mock data in the pubSubMockDb. This is used for testing so that we can know which message comes first'
    )
    type: str = Field(
        ...,
        description='Type of the mock data',
    )

    @field_validator("type", mode="before")
    @classmethod
    def validate_prod(cls, v):
        if v not in ['pubSub', 'request']:
            raise ValueError("Type must be either 'pubSub' or 'request'")
        return v

    def checkIfValid(self):
        difference = datetime.datetime.now(
            datetime.timezone.utc) - self.dateOfCreation
        if difference > datetime.timedelta(days=3):
            raise Exception(
                'Mock data is older than 3 days. Please update it by running pubSubMockDataGenerator.py in the repository of the service that created this mock data.'
            )

    def getData(self):
        if self.type == 'pubSub':
            return self.data['body']['message']['data']
        else:
            return self.data

    class Config:
        validate_assignment = True  # ← so that __setattr__ still runs

    def __setattr__(self, name, value):
        # if they're trying to change one of our locked fields _after_ init, block it:
        if name in ('dateOfCreation',
                    'createdByFunctionName') and name in self.__dict__:
            raise AttributeError(f"{name!r} is read-only")
        super().__setattr__(name, value)


def createMockData(mockData: MockData, pubSubMockDb: PubSubMockDb) -> MockData:
    pubSubMockDb.create(mockData.model_dump(by_alias=True),
                        AppConfig().projectName)


class PubSub():

    def __init__(self, credentials: service_account.Credentials = None):

        self.isProductionEnvironment = AppConfig().getIsProductionEnvironment()

        if credentials is not None and self.isProductionEnvironment:
            raise Exception(
                'Cannot use service account credentials in production environment'
            )

        # if server is run on development or test we use service account credentials
        if not self.isProductionEnvironment:
            self.projectId = credentials.project_id
            self.publisher = pubsub_v1.PublisherClient(credentials=credentials)
            self.subscriber = pubsub_v1.SubscriberClient(
                credentials=credentials)
        else:
            credentials, project_id = google.auth.default()
            self.publisher = pubsub_v1.PublisherClient(credentials=credentials)
            self.subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
            self.projectId = project_id

    def _checkIfTopicExists(self, topicName):
        topicPath = self.publisher.topic_path(self.projectId, topicName)
        try:
            self.publisher.get_topic(request={"topic": topicPath})
            return True
        except Exception as e:
            return False

    def publishMessage(
        self,
        message: str | dict,
        topicName: str = None,
        projectNameConsumers: list[str] = None,
        publishToPubSubMockDb=False,
        test=False,
    ):
        """Publish a message.

        Behaviors:
          - If running against real Pub/Sub (prod/test): only at the final step do we JSON-serialize (if dict) and encode to bytes.
          - If using local mock (publishToPubSubMockDb): we keep the original dict structure (no forced string conversion) so tests can assert on native JSON.

        Args:
          message: dict (preferred) or str. Dicts are preserved until serialization boundary.
        """

        if publishToPubSubMockDb and self.isProductionEnvironment:
            raise Exception(
                'Cannot publish to Pub/Sub mock database in production environment'
            )
        if not isinstance(message, (str, dict)):
            raise TypeError('message must be str or dict')

        if self.isProductionEnvironment or test:
            topicPath = self.publisher.topic_path(self.projectId, topicName)
            data_bytes = self._serialize_for_pubsub(message)
            attrs = {
                'originalTopicPath': topicPath,
            }
            future = self.publisher.publish(topicPath, data_bytes, **attrs)
            try:
                message_id = future.result(timeout=15)
                return {"status": "success", "messageId": message_id}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        elif publishToPubSubMockDb:
            if projectNameConsumers is None:
                raise ValueError(
                    "projectNameConsumers must be provided when using local Pub/Sub mock."
                )

            # create mock payload (store dict as-is; str stays str)
            gmt_plus_8 = datetime.timezone(datetime.timedelta(hours=8))
            now_in_gmt_plus_8 = datetime.datetime.now(gmt_plus_8)
            now_in_utc = now_in_gmt_plus_8.astimezone(datetime.timezone.utc)
            formatted_datetime = now_in_utc.isoformat(
                timespec='milliseconds').replace('+00:00', 'Z')
            mockMessageId = generateRandomString()
            req = {
                'body': {
                    'message': {
                        'data':
                        message,
                        'messageId':
                        mockMessageId,
                        'message_id':
                        mockMessageId,
                        'publishTime':
                        formatted_datetime,
                        'publish_time':
                        formatted_datetime
                    }
                }
            }
            createMockData(
                MockData(data=req,
                         projectNameConsumers=[
                             x.name for x in projectNameConsumers
                         ],
                         consumeFunctionName=topicName,
                         index=_getIndex(),
                         type='pubSub'), pubSubMockDb)
            return {"status": "mocked", "stored": True}
        elif not self.isProductionEnvironment:
            return {
                "status":
                "success",
                "message":
                "Not published since we are in local dev and publishToMockDb is False"
            }
        else:
            raise Exception("Invalid publish mode")

    def _serialize_for_pubsub(self, message: str | dict) -> bytes:
        """Serialize message to bytes for Pub/Sub.
        Dict -> JSON bytes. Str -> UTF-8 bytes.
        """
        if isinstance(message, dict):
            return self.convertToJson(message).encode('utf-8')
        if isinstance(message, str):
            return message.encode('utf-8')
        raise TypeError('Unsupported message type for serialization')

    def _maybe_parse_json_string(self, message: str | dict):
        if isinstance(message, dict):
            return message
        try:
            return json.loads(message)
        except Exception:
            return message

    def pushToTestGoogleCloudFunction(self, message):
        return self.publishMessage('test', message, test=True)

    # def _createMessageInTopicsDatabase(self,message):

    # Custom JSON serializer for datetime objects
    def convertToJson(self, message):

        def customSerializer(obj):
            # if isinstance(obj, bytes):
            #     return obj
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()  # Convert datetime to ISO format string
            raise TypeError(f"Type {type(obj)} is not serializable")

        res = json.dumps(message, default=customSerializer)
        return res

def decodeMessage(message):
    # Step 1: Decode the base64-encoded message
    decoded_message = base64.b64decode(message).decode('utf-8')

    # Step 2: Try to convert the decoded message to a JSON object
    try:
        # If it's a JSON string, convert it to a dictionary
        decoded_message = json.loads(decoded_message)
    except json.JSONDecodeError:
        # If it's not a JSON, keep the string as is
        pass

    return decoded_message


class TestPubSub(PubSub, Singleton):

    def __init__(self):
        # Use service account credentials for testing
        if not AppConfig().getIsProductionEnvironment():
            cwd = os.getcwd()
            keyPath = cwd + r'/server/keys/online-store-paperboy-92adc6ce5dc5.json'
            credentials = service_account.Credentials.from_service_account_file(
                keyPath)
        else:
            credentials= None
        super().__init__(credentials=credentials)


class MainPubSub(PubSub, Singleton):

    def __init__(self):

        if not AppConfig().getIsProductionEnvironment():
            cwd = os.getcwd()
            keyPath = cwd + r'/server/keys/starpack-b149d-ea86f6d0c9ec.json'
            credentials = service_account.Credentials.from_service_account_file(
                keyPath)
        else:
            credentials = None

        super().__init__(credentials=credentials)


pubSub = MainPubSub()
testPubSub = TestPubSub()


def pubSubDecorator(projectNameConsumers: list[AbstractService]):

    if projectNameConsumers is None:
        raise ValueError("projectNameConsumers parameter is required")
    for x in projectNameConsumers:
        if not isinstance(x, AbstractService):
            raise TypeError(
                "projectNameConsumers must contain only AbstractService instances"
            )

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound_args = sig.bind_partial(*args, **kwargs)
            publishToPubSubMockDb = bound_args.arguments.get(
                'publishToPubSubMockDb', False)
            result = func(*args, **kwargs)
            pubSub.publishMessage(
                result,
                projectNameConsumers=projectNameConsumers,
                publishToPubSubMockDb=publishToPubSubMockDb,
                topicName=f'{func.__name__}_{AppConfig().projectName}')
            return result

        return wrapper

    return decorator


class PubsubMessage(BaseModel):
    """
    Wire-format Pub/Sub message.

    Notes:
      - `data` is stored as raw bytes in the model.
      - When exporting to JSON, `data` is serialized to base64 (string),
        matching Pub/Sub’s REST/HTTP format.
      - `messageId` and `publishTime` are set by Pub/Sub (present on delivery).
      - `orderingKey` appears only if message ordering is enabled.
    """
    data: bytes = Field(default=b"", description="Raw payload; base64 in JSON")
    attributes: Dict[str, str] = Field(default_factory=dict)
    messageId: Optional[str] = None
    publishTime: Optional[datetime.datetime] = None
    orderingKey: Optional[str] = None

    # Accept data as bytes or base64 string
    @field_validator("data", mode="before")
    @classmethod
    def _decodeData(cls, v):
        if isinstance(v, bytes):
            message = PubSub().decodeMessage(v)
            if not isinstance(message, dict):
                raise TypeError('data must be a dictionary once decoded')
        raise TypeError("data must be bytes or base64 string")

    # Serialize bytes -> base64 string for JSON export
    @field_serializer("data")
    def _serialize_data(self, v: bytes, _info):
        return base64.b64encode(v).decode("ascii")


class MockDataConsumer(Singleton):

    def __init__(self):
        self.previousIndexConsumed = 0

    def consumeMockData(self, serviceProjectName: str, function: Callable,
                        index: int) -> None:

        if index != self.previousIndexConsumed:
            raise Exception(
                f'You cannot consume mock data with index {index}. You must consume mock data with index {self.previousIndexConsumed} first. This is to ensure that the mock data is consumed in the correct order.'
            )

        mockData = pubSubMockDb.read(
            {
                'consumeFunctionName': function.__name__,
                'index': index
            },
            serviceProjectName,
            findOne=True)

        if mockData == None:
            raise Exception(
                f'No mock data found for function {function.__name__} in project {serviceProjectName}'
            )

        mockData = MockData(**mockData)
        mockData.checkIfValid()
        data = mockData.getData()

        res = function(data)

        self.previousIndexConsumed += 1

        return {'res': res, 'message': data}


mockDataConsumer = MockDataConsumer()

if __name__ == '__main__':
    # Example usage
    data = {'hello': 'world'}
    data = PubSub().convertToJson(data)
    data = data.encode("utf-8")

    message = PubsubMessage(data=data, attributes={"key": "value"})
    print(message.model_dump())  # JSON representation with base64 data
