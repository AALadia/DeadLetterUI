from flask import Blueprint, jsonify, request
import logging
from mongoDb import mongoDb, db
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
        messageId = data["message"]["data"].get('messageId')
        originalMessage = data["message"]["data"].get('originalMessage')
        originalTopicPath = data["message"]["data"].get('originalTopicPath')
        originalMessage = data["message"]["data"]
        originalTopicPath=data["message"].get("attributes").get("originalTopicPath")
        messageId = data["message"]["messageId"]
        if db.read({"_id": messageId},"PubSubMessages",findOne=True):
            return jsonify({"message": "Message already processed","status":200,"data":None,"currentUser":None}), 200
    try:
        res = PubSubRequests().createDeadLetter(messageId, originalMessage, originalTopicPath)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'message': str(e),'data':None,'status':400}), 400

    try:
        db.create({"_id":messageId,"_version":0},"PubSubMessages")
    except:
        pass
    return jsonify({"message": "Dead letter message created successfully", "status":200, "data": res}), 200
