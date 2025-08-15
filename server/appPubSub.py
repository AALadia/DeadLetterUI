from flask import Blueprint, jsonify, request
import logging
from mongoDb import mongoDb
from PubSubRequests import PubSubRequests
import traceback
from pubSub import PubSub

main = Blueprint('main', __name__)
logging.basicConfig(level=logging.INFO)


@main.route('/createDeadLetter', methods=['POST'])

def createDeadLetter():
    if request.is_json:
        data = request.get_json()
        if isinstance(data["message"]["data"],str):
             data["message"]["data"] = PubSub().decodeMessage(data["message"]["data"])
        _id = data["message"]["data"].get('_id')
        originalMessage = data["message"]["data"].get('originalMessage')
        subscription = data["message"]["data"].get('subscription')
        subscription = data["subscription"]
        originalTopicPath = data["message"]["attributes"].get("originalTopicPath")
        originalMessage = data["message"]["data"]
    try:
        res = PubSubRequests().createDeadLetter(_id, originalMessage, subscription)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'message': str(e),'data':None,'status':400}), 400

    return jsonify({"message": "Dead letter message created successfully", "status":200, "data": res}), 200
