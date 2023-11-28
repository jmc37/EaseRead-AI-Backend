import os

from flask import Flask, jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from redis_client import create_redis_client


from dotenv import load_dotenv

from db import db
import models
import redis


from resources.users import blp as UserBlueprint
from resources.document import chat_bp as Chat
from resources.api import blp as API

# Creates app
def create_app(db_url=None):
    app = Flask(__name__)
    CORS(app, supports_credentials=True, allow_headers=["Content-Type", "Authorization"], resources={r"/API/v1/*": {"origins": ["http://127.0.0.1:5501", "https://easeread-frontend.onrender.com"]}})


    load_dotenv()

    app.config["API_TITLE"] = "API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/doc/"
    app.config[
        "OPENAPI_SWAGGER_UI_URL"
    ] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["PROPAGATE_EXCEPTIONS"] = True
    db.init_app(app)
    migrate = Migrate(app, db)
    api = Api(app)
    app.config["JWT_SECRET_KEY"] = os.getenv("SECRET")

    # Initialize Redis client
    redis_client = create_redis_client()

    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        token_key = f'token:{jwt_payload["jti"]}'
        return redis_client.exists(token_key)

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {"description": "The token has been revoked.",
                    "error": "token_revoked"}
            ),
            401,
        )

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"message": "The token has expired.", "error": "token_expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                {"message": "Signature verification failed.", "error": "invalid_token"}
            ),
            401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {
                    "description": "Request does not contain an access token.",
                    "error": "authorization_required",
                }
            ),
            401,
        )

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {"description": "The token is not fresh.",
                    "error": "fresh_token_required"}
            ),
            401,
        )

    api.register_blueprint(UserBlueprint)
    api.register_blueprint(Chat)
    api.register_blueprint(API)

    return app
