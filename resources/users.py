from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from db import db
from models import UserModel
from schemas import UserSchema
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from blocklist import BLOCKLIST
blp = Blueprint("Users", "users", description="Operations on users")


@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        if UserModel.query.filter(UserModel.username == user_data["username"]).first():
            abort(409, message="A user with that username already exists")
        user = UserModel(
            username=user_data["username"],
            password=pbkdf2_sha256.hash(user_data["password"])
        )
        db.session.add(user)
        db.session.commit()

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


@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message": "Successfully logged out."}
