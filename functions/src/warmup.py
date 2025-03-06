from firebase_functions import https_fn
import json
import requests
import os

@https_fn.on_request()
def warmup_function(request: https_fn.Request) -> https_fn.Response:
    """
    Warmup関数 - 定期的に呼び出されることでインスタンスを温める
    
    Args:
        request: Cloud Functionsのリクエストオブジェクト
        
    Returns:
        Response: 正常に実行できたことを示すレスポンス
    """
    print("***** Warmup function called to keep instances warm *****")
    
    # slack_bot_functionも温める
    try:
        # リージョンとプロジェクトIDを環境変数から取得（デプロイ時に自動的に設定される）
        region = os.environ.get('FUNCTION_REGION', 'us-central1')
        project_id = os.environ.get('GCP_PROJECT', 'slack-attendance-bot-4a3a5')
        
        # slack_bot_functionのURLを構築
        bot_function_url = f"https://{region}-{project_id}.cloudfunctions.net/slack_bot_function"
        
        # 簡単なGETリクエストを送信（実際の関数を呼び出さないようにするためのパス）
        warmup_response = requests.get(
            f"{bot_function_url}/warmup", 
            headers={"X-Warmup-Request": "true"},
            timeout=10
        )
        print(f"***** Warmed up slack_bot_function - Status: {warmup_response.status_code} *****")
    except Exception as e:
        print(f"***** Error warming up slack_bot_function: {str(e)} *****")
    
    # 簡単なレスポンスを返す
    return https_fn.Response(
        json.dumps({
            "status": "ok",
            "message": "Warmup function executed successfully"
        }),
        status=200,
        mimetype='application/json'
    )