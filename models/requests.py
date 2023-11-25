from db import db


class RequestModel(db.Model):
    __tablename__ = "requests"

    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.String(30), nullable=False)
    endpoint = db.Column(db.String, nullable=False)
    requests = db.Column(db.Integer, nullable=False, default=0)

