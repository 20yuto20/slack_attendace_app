import os
import json
from dotenv import load_dotenv
from firebase_functions import https_fn
from firebase_admin import initialize_app, credentials

from src.slack.app import create_slack_bot_function
from src.warmup import warmup_function  # Import the warmup function
from src.alerts import manual_attendance_alerts, attendance_alerts_function  # Explicitly import alert functions
from src.repositories.firestore_repository import FirestoreRepository
from src.config import get_config

# Load environment variables
load_dotenv()

# Initialize Firebase (only once)
try:
    cred_path = os.getenv('APP_FIREBASE_CREDENTIALS_PATH')
    if not cred_path:
        raise ValueError("Firebase credentials path not set in environment variables")
    
    if not os.path.exists(cred_path):
        raise FileNotFoundError(f"Firebase credentials file not found at: {cred_path}")
    
    cred = credentials.Certificate(cred_path)
    initialize_app(cred)
except Exception as e:
    print(f"Firebase initialization error: {str(e)}")
    raise

@https_fn.on_request()
def slack_bot_function(request: https_fn.Request) -> https_fn.Response:
    """
    Entry point for Slack bot
    
    Args:
        request: Cloud Functions request object
        
    Returns:
        Response: Cloud Functions response object
    """
    try:
        # Handle warmup request
        if request.path == "/warmup" and request.headers.get("X-Warmup-Request") == "true":
            print("***** Received warmup request for slack_bot_function *****")
            return https_fn.Response(
                json.dumps({
                    "status": "ok",
                    "message": "Warmup successful"
                }),
                status=200,
                mimetype='application/json'
            )
        
        # Process normal request
        return create_slack_bot_function(request)
    except Exception as e:
        print(f"Error in slack_bot_function: {str(e)}")
        return https_fn.Response(
            json.dumps({
                "error": "Internal Server Error",
                "message": str(e)
            }),
            status=500,
            mimetype='application/json'
        )

# Re-export the alert functions and warmup function
manual_attendance_alerts = manual_attendance_alerts
attendance_alerts_function = attendance_alerts_function
warmup_function = warmup_function