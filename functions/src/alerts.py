import json
from firebase_functions import https_fn, scheduler_fn
from slack_sdk import WebClient

from .repositories.firestore_repository import FirestoreRepository
from .services.warning_service import WarningService
from .config import get_config

def create_alert_function(repository: FirestoreRepository, client: WebClient = None):
    """
    勤怠警告チェック関数を作成
    
    Args:
        repository: Firestoreレポジトリ
        client: Slackクライアント（テスト用に注入可能）
    
    Returns:
        function: Cloud Function
    """
    
    config = get_config()
    warning_service = WarningService(repository)
    
    @scheduler_fn.on_schedule(schedule="every {interval} minutes".format(
        interval=getattr(config.attendance_alerts, 'check_interval_minutes', 30)
    ))
    def attendance_alerts_function(event: scheduler_fn.ScheduledEvent) -> None:
        """
        定期的に実行され、長時間勤務・長時間休憩のユーザーに警告を送信する
        
        Args:
            event: スケジュールイベント
        """
        try:
            # 警告機能が無効の場合は処理しない
            if not warning_service.is_alert_enabled():
                print("Attendance alerts are disabled in configuration")
                return
                
            print("Running attendance alerts check...")
            
            # すべてのワークスペースの警告対象者を取得
            # 将来的に複数ワークスペース対応を考慮
            workspaces = repository.get_all_workspaces()
            
            for workspace in workspaces:
                team_id = workspace.get('team_id')
                if not team_id:
                    continue
                    
                # 警告対象ユーザーを取得
                warnings = warning_service.get_all_warnings(team_id=team_id)
                
                if not warnings:
                    print(f"No warnings for workspace {team_id}")
                    continue
                
                print(f"Found {len(warnings)} warnings for workspace {team_id}")
                
                # Slackクライアントを初期化
                slack_client = client or WebClient(token=config.slack.bot_token)
                
                # 各ユーザーに警告を送信
                for warning in warnings:
                    try:
                        # 警告メッセージを整形
                        message = warning_service.format_warning_message(warning)
                        
                        # DMで警告を送信
                        slack_client.chat_postMessage(
                            channel=warning['user_id'],
                            text=message
                        )
                        
                        print(f"Sent warning to user {warning['user_id']} for {warning['warning_type']}")
                    except Exception as e:
                        print(f"Error sending warning to user {warning['user_id']}: {str(e)}")
            
            print("Attendance alerts check completed")
        except Exception as e:
            print(f"Error in attendance_alerts_function: {str(e)}")
    
    return attendance_alerts_function

# 手動実行用のHTTPエンドポイント（デバッグとテスト用）
@https_fn.on_request()
def manual_attendance_alerts(request: https_fn.Request) -> https_fn.Response:
    """
    手動で警告チェックを実行するためのエンドポイント
    デバッグ・テスト目的のみで使用
    
    Args:
        request: HTTPリクエスト
        
    Returns:
        Response: チェック結果
    """
    try:
        config = get_config()
        
        # APIキーによる認証（簡易的なセキュリティ）
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != config.get('debug_api_key', ''):
            return https_fn.Response(
                json.dumps({"error": "Unauthorized"}),
                status=401,
                mimetype='application/json'
            )
        
        # Firestoreレポジトリを初期化
        repository = FirestoreRepository(
            project_id=config.firebase.project_id,
            credentials_path=config.firebase.credentials_path
        )
        
        # 警告サービスを初期化
        warning_service = WarningService(repository)
        
        # すべての警告を取得
        warnings = warning_service.get_all_warnings()
        
        # 結果を返す
        return https_fn.Response(
            json.dumps({
                "success": True,
                "warnings": len(warnings),
                "details": [
                    {
                        "user_id": w["user_id"],
                        "user_name": w["user_name"],
                        "warning_type": w["warning_type"],
                        "duration": w["duration"]
                    } for w in warnings
                ]
            }),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        return https_fn.Response(
            json.dumps({
                "error": "Internal Server Error",
                "message": str(e)
            }),
            status=500,
            mimetype='application/json'
        )