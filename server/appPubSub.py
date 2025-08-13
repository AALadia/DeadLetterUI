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
        data["message"]["data"] = PubSub().decodeMessage(data["message"]["data"])
        _id = data["message"]["data"]['_id']
        originalMessage = data["message"]["data"]['originalMessage']
        topicName = data["message"]["data"]['topicName']
        subscriberName = data["message"]["data"]['subscriberName']
        endpoint = data["message"]["data"]['endpoint']
        errorMessage = data["message"]["data"]['errorMessage']
        topicName = data["message"]["attributes"]["topicName"]
        subscriberName = data["subscription"]
        endpoint = ""
        errorMessage = ""
        print(data)
        publisherProjectId = data["message"]["attributes"]["publisherProjectId"]
        publisherProjectName = data["message"]["attributes"]["publisherProjectName"]
    try:
        res = PubSubRequests().createDeadLetter(_id, originalMessage, topicName, subscriberName, endpoint, errorMessage)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'message': str(e),'data':None,'status':400}), 400

    return jsonify({"message": "Dead letter message created successfully", "status":200, "data": res}), 200
