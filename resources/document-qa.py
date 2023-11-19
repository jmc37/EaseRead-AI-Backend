from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from db import db
from models import UserModel
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from blocklist import BLOCKLIST
from transformers import pipeline
from PIL import Image
import base64
from io import BytesIO
from flask import request

blp = Blueprint("Users", "users", description="Operations on users")

# Initialize the pipeline outside the route to reuse it for multiple requests
document_qa_pipe = pipeline("document-question-answering", model="impira/layoutlm-document-qa")

@blp.route("/document_qa")
class DocumentQA(MethodView):
    @jwt_required()
    @blp.response(200)
    def post(self):
        # Get question and file directly from the request object
        question = request.form.get('question')
        uploaded_file = request.files.get('file')

        # Save the uploaded image to a file
        image_path = "static/uploads/user_image.png"
        uploaded_file.save(image_path)

        # Process the image and question using the document-question-answering model
        image = Image.open(image_path)
        result = document_qa_pipe(image=image, question=question)

        # Convert image to base64 for displaying in HTML (optional)
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()

        # Return the result, and optionally the image
        return {"result": result[0]['answer'], "image": img_str}

# Your existing routes...
# ...

# Add the blueprint to your Flask app
blp.register_to(app)

if __name__ == '__main__':
    app.run(debug=True)
