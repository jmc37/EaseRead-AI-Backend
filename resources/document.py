from flask import request, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
import os
import requests
from db import db
from models import RequestModel
API_VERSION = "/API/v1"


chat_bp = Blueprint("Chat", "chat", description="Operations on chat")

# Hugging Face API URL and headers
HUGGING_FACE_API_URL = "https://hzueekj3hyei2n49.us-east-1.aws.endpoints.huggingface.cloud"
HUGGING_FACE_HEADERS = {
    "Authorization": f"Bearer {os.getenv('AI_TOKEN')}",
    "Content-Type": "application/json"
}

# Function to make the Hugging Face API call
def query_hugging_face(payload):
    response = requests.post(HUGGING_FACE_API_URL, headers=HUGGING_FACE_HEADERS, json=payload)
    return response.json()

# Define your views and routes within this blueprint
@chat_bp.route(f"{API_VERSION}/chat", methods=["POST"])
class ChatView(MethodView):
    # @jwt_required()
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

             # Increment the requests count in the routes table by 1
            route = RequestModel.query.filter_by(method='POST', endpoint=f'{API_VERSION}/chat').first()
            if route:
                route.requests += 1
                db.session.commit()
            # Create a Flask response with CORS headers
            response = jsonify({"answer": hugging_face_response[0].get("generated_text").replace("\n", "<br>")})
            
            # Add CORS headers to the response
            response.headers.add('Access-Control-Allow-Origin', 'https://easeread-frontend.onrender.com')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'OPTIONS, POST')
            return response

        except Exception as e:
            print("Error during processing:", e)
            return jsonify({"error": "Error during processing"}), 500
