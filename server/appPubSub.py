from flask import Blueprint, jsonify, request
import logging
from mongoDb import mongoDb
from PubSubRequests import PubSubRequests
import traceback

main = Blueprint('main', __name__)
logging.basicConfig(level=logging.INFO)


@main.route('/createAccountingInventoryOrder', methods=['POST'])

def createAccountingInventoryOrder():
    if request.is_json:
        data = request.get_json()
        order = data['order']
    try:
        res = PubSubRequests().createAccountingInventoryOrder(order)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'message': str(e),'data':None,'status':400}), 400

    return jsonify({"message": "Order created successfully", "status":200, "data": res}), 200
