from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from AppConfig import AppConfig
from objects import *
from ApiRequests import ApiRequests
import os
import logging
from appPubSub import main
from flask_jwt_extended import (JWTManager, create_access_token, jwt_required, get_jwt_identity)
from Settings import DatabaseSettingUpdater
from datetime import timedelta
import traceback

app = Flask(__name__)
app.register_blueprint(main)
if os.getenv("JWT_SECRET_KEY") == None:
    raise ValueError("JWT_SECRET_KEY environment variable is not set")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
jwt = JWTManager(app)
CORS(app, resources={r"/*": {"origins": "*"}})
logging.basicConfig(level=logging.INFO)


@app.route('/setUserRole', methods=['POST'])
@jwt_required()
def setUserRole():
    if request.is_json:
        data = request.get_json()
        userIdToChangeRole = data.get('userIdToChangeRole')
        userType = data.get('userType')
        userId = data.get('userId')
        current_user = get_jwt_identity()
    try:
        res = ApiRequests().setUserRole(userIdToChangeRole, userType, userId)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'message': str(e),'data':None,'status':400}), 400

    return jsonify({"message": "User role updated successfully","status":200, "current_user": current_user, "data": res}), 200


@app.route('/setSpecificRoles', methods=['POST'])
@jwt_required()
def setSpecificRoles():
    if request.is_json:
        data = request.get_json()
        userIdToChangeRole = data.get('userIdToChangeRole')
        roleId = data.get('roleId')
        value = data.get('value')
        userId = data.get('userId')
        current_user = get_jwt_identity()
    try:
        res = ApiRequests().setSpecificRoles(userIdToChangeRole, roleId, value, userId)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'message': str(e),'data':None,'status':400}), 400

    return jsonify({"message": "User role updated successfully","status":200, "current_user": current_user, "data": res}), 200


@app.route('/fetchUserList', methods=['POST'])
@jwt_required()
def fetchUserList():
    if request.is_json:
        data = request.get_json()
        projection = data.get('projection')
        current_user = get_jwt_identity()
    try:
        res = ApiRequests().fetchUserList(projection)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'message': str(e),'data':None,'status':400}), 400

    return jsonify({"message": "User list fetched successfully","status":200, "current_user": current_user, "data": res}), 200


@app.route('/replayDeadLetter', methods=['POST'])
@jwt_required()
def replayDeadLetter():
    if request.is_json:
        data = request.get_json()
        deadLetterId = data.get('deadLetterId')
        userId = data.get('userId')
        current_user = get_jwt_identity()
    try:
        res = ApiRequests().replayDeadLetter(deadLetterId, userId)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'message': str(e),'data':None,'status':400}), 400

    return jsonify({"message": "Dead letter message updated successfully","status":200, "current_user": current_user, "data": res}), 200


@app.route('/closeDeadLetter', methods=['POST'])
@jwt_required()
def closeDeadLetter():
    if request.is_json:
        data = request.get_json()
        deadLetterId = data.get('deadLetterId')
        userId = data.get('userId')
        current_user = get_jwt_identity()
    try:
        res = ApiRequests().closeDeadLetter(deadLetterId, userId)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'message': str(e),'data':None,'status':400}), 400

    return jsonify({"message": "Dead letters fetched successfully","status":200, "current_user": current_user, "data": res}), 200


@app.route('/listDeadLetters', methods=['POST'])
@jwt_required()
def listDeadLetters():
    if request.is_json:
        data = request.get_json()
        projection = data.get('projection')
        current_user = get_jwt_identity()
    try:
        res = ApiRequests().listDeadLetters(projection)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'message': str(e),'data':None,'status':400}), 400

    return jsonify({"message": "Dead letters fetched successfully","status":200, "current_user": current_user, "data": res}), 200


@app.route('/loginWithGoogle', methods=['POST'])

def loginWithGoogle():
    if request.is_json:
        data = request.get_json()
        firebaseUserObject = data.get('firebaseUserObject')
    try:
        res = ApiRequests().loginWithGoogle(firebaseUserObject)
        access_token = create_access_token(identity=res["_id"])
    except Exception as e:
        traceback.print_exc()
        return jsonify({'message': str(e),'data':None,'status':400}), 400

    return jsonify({"message": "Login successful","data":res,"status":200, "access_token": access_token}), 200


@app.route('/mockPost', methods=['POST'])

def mockPost():
    if request.is_json:
        data = request.get_json()
        message = data.get('message')
    try:
        res = ApiRequests().mockPost(message)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'message': str(e),'data':None,'status':400}), 400

    return jsonify({"message": "Mock server response created successfully", "status":200, "data": res}), 200

if __name__ == '__main__':
    if (AppConfig().getIsDevEnvironment()):
        print(f"[92m_______________________{AppConfig().getEnvironment().upper()}_______________________[0m")
    if AppConfig().getIsProductionEnvironment():
        print(f"[91m_______________________{AppConfig().getEnvironment().upper()}_______________________[0m")

    from Settings import DatabaseSettingUpdater
    DatabaseSettingUpdater().updateDatabaseSettingsToDefault()

    if AppConfig().getisLocalEnvironment():
        app.run(debug=False, host='0.0.0.0', port=5000)
    else:
        app.run(host='0.0.0.0', port=8080)
