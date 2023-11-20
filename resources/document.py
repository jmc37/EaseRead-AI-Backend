from flask.views import MethodView
from flask_smorest import Blueprint
from flask import request, jsonify
import requests  # Import the requests module
from schemas import DocumentQARequestSchema

blp = Blueprint("Document", "document", description="Document upload")

@blp.route("/document_qa")
class DocumentQA(MethodView):
    @blp.arguments(DocumentQARequestSchema)
    @blp.response(200)
    def post(self):  # Change from put to post
        try:
            data = request.get_json()

            # Define headers
            headers = {
                'Authorization': 'Bearer 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',
                'Content-Type': 'application/json',
            }

            # Make a POST request to the Hugging Face API
            response = requests.post('https://hzueekj3hyei2n49.us-east-1.aws.endpoints.huggingface.cloud', json=data, headers=headers)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                result = response.json()
                return jsonify(result)
            else:
                # Handle non-200 status codes appropriately
                return jsonify({"error": f"Request failed with status code {response.status_code}"}), response.status_code

        except Exception as e:
            # Log the error for debugging
            print(f"Error during processing: {str(e)}")
            return jsonify({"error": "Internal Server Error"}), 500
