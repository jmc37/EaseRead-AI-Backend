import os
import requests
from flask.views import MethodView
from flask import jsonify, make_response
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from db import db
from models import UserModel, RequestModel
from schemas import UserSchema, UserRegisterSchema
from redis_client import create_redis_client
from flask_jwt_extended import create_access_token, jwt_required, get_jwt,decode_token
from datetime import datetime, timedelta
from sqlalchemy import or_
from flask_cors import cross_origin
from flask import request

API_VERSION = "/API/v1"
blp = Blueprint("Users", "users", description="Operations on users")

redis_client = create_redis_client()

domain = os.getenv("MAILGUN_DOMAIN")
def send_simple_message(to, subject, body):
	return requests.post(
		f"https://api.mailgun.net/v3/{domain}/messages",
		auth=("api", os.getenv("MAILGUN_API_KEY")),
		data={"from": "EaseRead AI Team <mailgun@{domain}>",
			"to": [to],
			"subject": subject,
			"text": body})

@blp.route(f"{API_VERSION}/register")
class UserRegister(MethodView):
    @blp.arguments(UserRegisterSchema)
    def post(self, user_data):
        if UserModel.query.filter(
            or_(
            UserModel.username == user_data["username"], 
            UserModel.email ==user_data["email"] 
            )
            ).first():
            abort(409, message="A user with that username or email already exists")
        user = UserModel(
            username=user_data["username"],
            name=user_data["name"],
            email=user_data["email"],
            password=pbkdf2_sha256.hash(user_data["password"]),
        )
        route = RequestModel.query.filter_by(method='POST', endpoint=f'{API_VERSION}/register').first()
        if route:
            route.requests += 1
        db.session.add(user)
        db.session.commit()

        send_simple_message(
            to=user.email,
            subject="Succesfully Signed Up",
            body=f"Hi {user.name}! You have sucessfully signed up for EaseRead API"
        )
        return {"message": "User created successfully."}, 201


@blp.route(f"{API_VERSION}/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        expiration_time = datetime.utcnow() + timedelta(seconds=1800)
        user = UserModel.query.filter(
            UserModel.username == user_data["username"]).first()

        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            additional_claims = {"username": user.username, "admin": user.admin}
            access_token = create_access_token(identity=user.username, additional_claims=additional_claims)
            user.requests += 1
            route = RequestModel.query.filter_by(method='POST', endpoint=f'{API_VERSION}/login').first()
            if route:
                route.requests += 1
            db.session.commit()

            # Create a JSON response
            response = make_response({"access_token": access_token})

            # Set the access token as an HTTP cookie
            response.set_cookie(
            'access_token',
            value=access_token,
            max_age=1800,  # Set the max_age to 1800 seconds (30 minutes)
            expires=expiration_time.strftime("%a, %d %b %Y %H:%M:%S GMT"),  # Format expiration time as RFC 1123 string
            httponly=True,
            secure=True,
            samesite='None',  # Add SameSite attribute
        )
            # Set Access-Control-Allow-Credentials header
            # response.headers.add("Access-Control-Allow-Credentials", "true")
            print(response)
            return response
        abort(401, message="Invalid credentials.")

@blp.route(f"{API_VERSION}/users")
class UsersList(MethodView):
    @blp.response(200, UserSchema(many=True))
    def get(self):
        route = RequestModel.query.filter_by(method='GET', endpoint=f'{API_VERSION}/users').first()
        if route:
            route.requests += 1
        db.session.commit()

        access_token_cookie = request.cookies.get('access_token')
        # Decode the token using the secret key
        decoded_token = decode_token(access_token_cookie)

        is_admin = decoded_token.get("admin", False)

        if not is_admin:
            abort(401, message="Admin privilege required")
        users = UserModel.query.all()
        return users

@blp.route(f"{API_VERSION}/userRequests")
class User(MethodView):
    @cross_origin(supports_credentials=True)
    @blp.response(200, UserSchema)
    def get(self):
        route = RequestModel.query.filter_by(method='GET', endpoint=f'{API_VERSION}/userRequests').first()
        if route:
            route.requests += 1
        access_token_cookie = request.cookies.get('access_token')
        # Decode the token using the secret key
        decoded_token = decode_token(access_token_cookie)

        username = decoded_token['username']
        user = UserModel.query.filter_by(username=username).first_or_404()
        user.requests += 1
        db.session.commit()
        # Include the number of API requests in the response
        response = jsonify({"api_requests": user.requests})


        return response

@blp.route(f"{API_VERSION}/user/<int:user_id>")
class User(MethodView):    
    def delete(self, user_id):
        route = RequestModel.query.filter_by(method='DELETE', endpoint=f'{API_VERSION}/user/<int:user_id>').first()
        if route:
            route.requests += 1
        # Access the access_token cookie
        access_token_cookie = request.cookies.get('access_token')
        # Decode the token using the secret key
        decoded_token = decode_token(access_token_cookie)

        is_admin = decoded_token.get("admin", False)  # Default to False if "is_admin" is not present
        if not is_admin:
            abort(401, message="Admin privilege required")
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted"}, 200

    def put(self, user_id):
        route = RequestModel.query.filter_by(method='PUT', endpoint=f'{API_VERSION}/user/<int:user_id>').first()
        if route:
            route.requests += 1
        
        # Access the access_token cookie
        access_token_cookie = request.cookies.get('access_token')
        # Decode the token using the secret key
        decoded_token = decode_token(access_token_cookie)

        is_admin = decoded_token.get("admin", False)

        if not is_admin:
            abort(401, message="Admin privilege required")

        user = UserModel.query.get_or_404(user_id)
        user.admin = True
        db.session.commit()

        return {"message": "User is now an admin"}, 200

    def patch(self, user_id):
        route = RequestModel.query.filter_by(method='PATCH', endpoint=f'{API_VERSION}/user/<int:user_id>').first()
        if route:
            route.requests += 1
        # Access the access_token cookie
        access_token_cookie = request.cookies.get('access_token')
        # Decode the token using the secret key
        decoded_token = decode_token(access_token_cookie)
        is_admin = decoded_token.get("admin", False)

        if not is_admin:
            abort(401, message="Admin privilege required")

        user = UserModel.query.get_or_404(user_id)
        user.admin = False
        db.session.commit()

        return {"message": "User is no longer an admin"}, 200


@blp.route(f"{API_VERSION}/logout")
class UserLogout(MethodView):
    @cross_origin(supports_credentials=True)
    def post(self):
        route = RequestModel.query.filter_by(method='POST', endpoint=f'{API_VERSION}/logout').first()
        if route:
            route.requests += 1
        db.session.commit()

        # Access the access_token cookie
        access_token_cookie = request.cookies.get('access_token')
        # Decode the token using the secret key
        decoded_token = decode_token(access_token_cookie)

        jti = decoded_token["jti"]
        redis_key = f'token:{jti}'
        expiration_time = decoded_token["exp"] - decoded_token["iat"] 
        # Store the token in Redis with an expiration time
        try:
            redis_client.setex(redis_key, expiration_time, "revoked")
        except Exception as e:
            # Handle the exception (e.g., log an error message)
            return jsonify({"error": e}), 500
        
        # Remove the access token cookie
        response = make_response({"message": "Successfully logged out."})
        response.delete_cookie('access_token')
        return response

# admin dashboard in progress --- set
@blp.route(f"{API_VERSION}/admin-dashboard")
class AdminDashboard(MethodView):
    @cross_origin(supports_credentials=True)
    def get(self):
        route = RequestModel.query.filter_by(method='GET', endpoint=f'{API_VERSION}/admin-dashboard').first()
        if route:
            route.requests += 1
        db.session.commit()

        # Access the access_token cookie
        access_token_cookie = request.cookies.get('access_token')

        try:
            # Decode the token using the secret key
            decoded_token = decode_token(access_token_cookie)

            # Access the username from the decoded token
            current_username = decoded_token['sub']

            # Fetch the user from the database based on the username
            # and check if the user has admin privileges.
            user = UserModel.query.filter_by(username=current_username).first()

            if user and user.admin:
                return jsonify(is_admin=True)
            else:
                return jsonify(is_admin=False)

        except Exception as e:
            # Handle token decoding failure (e.g., log an error message)
            return jsonify({"error": f"Token decoding failed: {e}"}), 401