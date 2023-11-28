import os
from flask.views import MethodView
from flask import jsonify
from flask_smorest import Blueprint, abort
from db import db
from models import UserModel, RequestModel
from flask_jwt_extended import jwt_required, get_jwt
from flask_cors import cross_origin

API_VERSION = "/API/v1"
blp = Blueprint("API", "api", description="Operations on api count")

@blp.route(f"{API_VERSION}/userapi")
class UsersList(MethodView):
    @jwt_required()
    @blp.response(200, UserSchema(many=True))
    def get(self):
        # Your existing code for user API data retrieval
        jwt = get_jwt()
        users = UserModel.query.all()
        return users

@blp.route(f"{API_VERSION}/allapi")
class AllAPIRoutes(MethodView):
    @jwt_required()
    @blp.response(200, description="Get all API routes")
    def get(self):
        jwt = get_jwt()
        is_admin = jwt.get("is_admin", False)

        if not is_admin:
            abort(401, message="Admin privilege required")

        # Query all unique API routes recorded in the RequestModel
        api_routes = (
            db.session.query(RequestModel)
            .distinct(RequestModel.endpoint)
            .all()
        )

        # Construct a response object
        api_routes_data = [
            {
                "id": route.id,
                "method": route.method,
                "endpoint": route.endpoint,
                "requests": route.requests,
            }
            for route in api_routes
        ]

        return jsonify(api_routes_data)
