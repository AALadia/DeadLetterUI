"""
Send mock data to PubSubRequests().createDeadLetter
Run from server dir with venv activated: python check_endpoints.py
"""
from PubSubRequests import PubSubRequests
from utils import generateRandomString

topic_path = "projects/online-store-paperboy/topics/createSalesOrder"
message_id = f"test-{generateRandomString()}"
original_message = {
    "orderId": "TEST-001",
    "customer": "Test Customer",
    "items": [{"sku": "ABC123", "qty": 1}],
}

print(f"Topic path:       {topic_path}")
print(f"Message ID:       {message_id}")
print(f"Original message: {original_message}")
print("-" * 60)

try:
    res = PubSubRequests().createDeadLetter(
        messageId=message_id,
        originalMessage=original_message,
        originalTopicPath=topic_path,
    )
    print("SUCCESS")
    print(f"  endPoints:    {res.get('endPoints')}")
    print(f"  status:       {res.get('status')}")
    print(f"  errorMessage: {res.get('errorMessage')}")
except Exception as e:
    print(f"ERROR: {e}")
