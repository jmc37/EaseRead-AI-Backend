from db import db


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80), unique=False, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)
    requests = db.Column(db.Integer, nullable=False, default=1)
