from marshmallow import Schema, fields

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True) #Doesn't return password
    admin = fields.Bool()

class DocumentQARequestSchema(Schema):
    inputs = fields.String(required=True)

class UserRegisterSchema(UserSchema):
    email=fields.Str(required=True)
    name=fields.Str(required=True)
