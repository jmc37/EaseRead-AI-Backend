from flask.views import MethodView
from flask_smorest import Blueprint, abort
from transformers import pipeline
from flask_jwt_extended import jwt_required
from PIL import Image
import base64
from io import BytesIO
from flask import request

blp = Blueprint("Document", "document", description="Document upload")

# Initialize the pipeline outside the route to reuse it for multiple requests
document_qa_pipe = pipeline("document-question-answering", model="impira/layoutlm-document-qa")

@blp.route("/document_qa")
class DocumentQA(MethodView):
    @jwt_required()
    @blp.arguments(DocumentQARequestSchema)  # Assuming you have a schema for the request data
    @blp.response(200)
    def post(self, document_qa_data):
        try:
            # Extract data from the request schema
            question = document_qa_data.get('question')
            uploaded_file = document_qa_data.get('file')

            if not question or not uploaded_file:
                abort(400, message="Missing question or file in the request")

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
        except Exception as e:
            print(f"Error processing document QA: {e}")
            abort(500, message="Internal Server Error")

# Add the blueprint to your Flask app
blp.register_to(app)

if __name__ == '__main__':
    app.run(debug=True)
