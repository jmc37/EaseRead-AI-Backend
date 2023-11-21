from flask import request, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
import requests


chat_bp = Blueprint("Chat", "chat", description="Operations on chat")

# Hugging Face API URL and headers
HUGGING_FACE_API_URL = "https://hzueekj3hyei2n49.us-east-1.aws.endpoints.huggingface.cloud"
HUGGING_FACE_HEADERS = {
    "Authorization": "Bearer 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",
    "Content-Type": "application/json"
}

# Function to make the Hugging Face API call
def query_hugging_face(payload):
    response = requests.post(HUGGING_FACE_API_URL, headers=HUGGING_FACE_HEADERS, json=payload)
    return response.json()

# Define your views and routes within this blueprint
@chat_bp.route("/chat", methods=["POST"])
class ChatView(MethodView):
    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            question = data.get("question")

            # Create the payload for the Hugging Face API call
            payload = {
                "inputs": question,
                "parameters": {
                    "repetition_penalty": 4.0,
                    "max_time": 60,
                    "max_new_tokens": 300,
                    "use_cache": False,
                    "temperature": 0.8
                }
            }

            # Make the Hugging Face API call
            hugging_face_response = query_hugging_face(payload)

            # Process the response as needed (you can log it or return it to the frontend)
            print("Response from Hugging Face API:", hugging_face_response)

            return jsonify({"answer": hugging_face_response[0].get("generated_text").replace("\n", "<br>")})

        except Exception as e:
            print("Error during processing:", e)
            return jsonify({"error": "Error during processing"}), 500

# Add this line at the end of your existing code to register the new endpoint
chat_bp.add_url_rule("/chat", view_func=ChatView.as_view("chat"))
