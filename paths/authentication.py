import uuid
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort

blp = Blueprint("Users", __name__, description="Operation on users")
@app.get("/signup")
def signup():
        return {"message": "signed up"}