import os
import json
from dotenv import load_dotenv
from firebase_functions import https_fn
from firebase_admin import initialize_app, credentials

from src.slack.app import create_slack_bot_function
from src.warmup import warmup_function  # Import the warmup function

# 環境変数の読み込み
load_dotenv()

# Firebase認証情報の設定
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
    Slackボットのエントリーポイント関数
    
    Args:
        request: Cloud Functionsのリクエストオブジェクト
        
    Returns:
        Response: Cloud Functionsのレスポンスオブジェクト
    """
    try:
        # ウォームアップリクエストの場合は処理せずにOKを返す
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
        
        # 通常のリクエストは全てcreate_slack_bot_functionで処理
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