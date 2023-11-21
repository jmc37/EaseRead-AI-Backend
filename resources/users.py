import os
import requests
from flask.views import MethodView
from flask import jsonify
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from db import db
from models import UserModel
from schemas import UserSchema, UserRegisterSchema
from redis_client import create_redis_client
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from sqlalchemy import or_
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

@blp.route("/register")
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
            password=pbkdf2_sha256.hash(user_data["password"])
        )
        db.session.add(user)
        db.session.commit()

        send_simple_message(
            user=user.email,
            subject="Succesfully Signed Up",
            body=f"Hi {user.name}! You have sucessfully signed up for EaseRead API"
        )
        return {"message": "User created successfully."}, 201


@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter(
            UserModel.username == user_data["username"]).first()

        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=user.admin)
            return {"access_token": access_token}
        abort(401, message="Invalid credentials.")

@blp.route("/users")
class UsersList(MethodView):
    @jwt_required()
    @blp.response(200, UserSchema(many=True))
    def get(self):
        jwt = get_jwt()
        is_admin = jwt.get("is_admin", False)

        if not is_admin:
            abort(401, message="Admin privilege required")

        users = UserModel.query.all()
        return users


@blp.route("/user/<int:user_id>")
class User(MethodView):
    @blp.response(200, UserSchema)
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user
    
    @jwt_required()
    def delete(self, user_id):
        jwt = get_jwt()
        is_admin = jwt.get("is_admin", False)  # Default to False if "is_admin" is not present
        if not is_admin:
            abort(401, message="Admin privilege required")
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted"}, 200

    @jwt_required()
    def put(self, user_id):
        jwt = get_jwt()
        is_admin = jwt.get("is_admin", False)

        if not is_admin:
            abort(401, message="Admin privilege required")

        user = UserModel.query.get_or_404(user_id)
        user.admin = True
        db.session.commit()

        return {"message": "User is now an admin"}, 200

    @jwt_required()
    def patch(self, user_id):
        jwt = get_jwt()
        is_admin = jwt.get("is_admin", False)

        if not is_admin:
            abort(401, message="Admin privilege required")

        user = UserModel.query.get_or_404(user_id)
        user.admin = False
        db.session.commit()

        return {"message": "User is no longer an admin"}, 200
    
@blp.route("/admin-dashboard")
class AdminDashboard(MethodView):
    @jwt_required()
    def get(self):
        jwt_data = get_jwt()
        is_admin = jwt_data.get("is_admin", False)

        if is_admin:
            return jsonify(is_admin=True)
        else:
            return jsonify(is_admin=False)

@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        redis_key = f'token:{jti}'
        expiration_time = get_jwt()["exp"] - get_jwt()["iat"]
        
        # Store the token in Redis with an expiration time
        try:
            redis_client.setex(redis_key, expiration_time, "revoked")
        except Exception as e:
            # Handle the exception (e.g., log an error message)
            return jsonify({"error": e}), 500


        return jsonify({"message": "Successfully logged out."})
