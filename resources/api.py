import os
from flask.views import MethodView
from flask import jsonify, make_response
from flask_smorest import Blueprint, abort
from db import db
from models import UserModel, RequestModel
from schemas import UserSchema, UserRegisterSchema
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from datetime import datetime, timedelta
from sqlalchemy import or_
from flask_cors import cross_origin
from flask import request

API_VERSION = "/API/v1"
blp = Blueprint("API", "api", description="Operations on api count")

@blp.route(f"{API_VERSION}/userapi")
class UsersList(MethodView):
    @jwt_required()
    @blp.response(200, UserSchema(many=True))
    def get(self):
        route = RequestModel.query.filter_by(method='GET', endpoint=f'{API_VERSION}/users').first()
        jwt = get_jwt()
        users = UserModel.query.all()
        return users
    
@blp.route(f"{API_VERSION}/allapi")
class AllAPIRoutes(MethodView):
    @jwt_required()
    @blp.response(200, description="Get all API routes")
    def get(self):
        # Query all unique API routes recorded in the RequestModel
        jwt = get_jwt()
        is_admin = jwt.get("is_admin", False)

        if not is_admin:
            abort(401, message="Admin privilege required")
        # Extract endpoints from the result
        api_routes = db.session.query(RequestModel.endpoint).distinct().all()
        api_routes = [route[0] for route in api_routes]

        return jsonify(api_routes)