import os
import json
import logging
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

# ロギング設定
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Firebase (only once)
try:
    cred_path = os.getenv('APP_FIREBASE_CREDENTIALS_PATH')
    if not cred_path:
        raise ValueError("Firebase credentials path not set in environment variables")
    
    if not os.path.exists(cred_path):
        raise FileNotFoundError(f"Firebase credentials file not found at: {cred_path}")
    
    cred = credentials.Certificate(cred_path)
    initialize_app(cred)
    logger.info("Firebase initialized successfully")
except Exception as e:
    logger.error(f"Firebase initialization error: {str(e)}", exc_info=True)
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
        # リクエスト情報をログに記録
        logger.info(f"Received request: {request.method} {request.path}")
        
        # ユーザーエージェントを確認（デバッグ用）
        user_agent = request.headers.get('User-Agent', '')
        if 'Slackbot' in user_agent:
            logger.info("Request from Slackbot")
        
        # Handle warmup request
        if request.path == "/warmup" and request.headers.get("X-Warmup-Request") == "true":
            logger.info("***** Received warmup request for slack_bot_function *****")
            return https_fn.Response(
                json.dumps({
                    "status": "ok",
                    "message": "Warmup successful"
                }),
                status=200,
                mimetype='application/json'
            )
        
        # Slack OAuth処理のために特定のパスを処理
        if request.path in ["/slack/install", "/slack/oauth_redirect", "/slack/oauth_success", "/slack/oauth_failure"]:
            logger.info(f"Processing Slack OAuth path: {request.path}")
            if request.method == "GET" and request.path == "/slack/oauth_redirect":
                # QueryパラメータをログにOAuth redirectデバッグ用
                logger.info(f"OAuth redirect params: {dict(request.args)}")
                
                # コードパラメータが存在し、stateパラメータが空かどうかをチェック
                if 'code' in request.args and ('state' not in request.args or not request.args.get('state')):
                    logger.warning("State parameter is missing or empty in OAuth redirect - will use custom handler")
        
        # Process normal request
        return create_slack_bot_function(request)
    except Exception as e:
        logger.error(f"Error in slack_bot_function: {str(e)}", exc_info=True)
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