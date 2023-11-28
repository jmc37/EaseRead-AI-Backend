import os
from flask.views import MethodView
from flask import jsonify
from flask_smorest import Blueprint, abort
from db import db
from models import UserModel, RequestModel
from flask_jwt_extended import jwt_required, get_jwt,decode_token
from flask_cors import cross_origin
from flask import request

API_VERSION = "/API/v1"
blp = Blueprint("API", "api", description="Operations on api count")

@blp.route(f"{API_VERSION}/allapi")
class AllAPIRoutes(MethodView):
    @blp.response(200, description="Get all API routes")
    def get(self):
        # Access the access_token cookie
        access_token_cookie = request.cookies.get('access_token')
        # Decode the token using the secret key
        decoded_token = decode_token(access_token_cookie)
        is_admin = decoded_token.get("admin", False)

        if not is_admin:
            abort(401, message="Admin privilege required")

        # Query all unique API routes recorded in the RequestModel
        requests = RequestModel.query.all()

        # Convert the list of RequestModel instances to a list of dictionaries
        requests_data = [
            {
                "id": request.id,
                "method": request.method,
                "endpoint": request.endpoint,
                "requests": request.requests,
                # Add more attributes as needed, ensuring they are JSON serializable
            }
            for request in requests
        ]

        return jsonify(requests_data)
