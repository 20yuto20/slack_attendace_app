from firebase_admin import firestore
from flask import Request, Response, redirect
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
import json
import secrets
import os
import logging

from src.services.attendance_service import AttendanceService
from src.services.monthly_summary_service import MonthlySummaryService
from src.services.status_service import StatusService
from src.services.warning_service import WarningService
from src.slack.commands.attendance_commands import AttendanceCommands
from src.slack.commands.summary_commands import SummaryCommands
from src.slack.commands.status_commands import StatusCommands
from src.slack.oauth import setup_oauth_flow
from src.slack.custom_oauth import CustomOAuthHandler
from src.repositories.firestore_repository import FirestoreRepository
from src.config import get_config
from src.slack.events import handle_bot_invited_to_channel

# グローバルロガー設定
logger = logging.getLogger(__name__)

def create_slack_bot_function(request: Request) -> Response:
    """Create and return the Slack bot function"""
    try:
        # ロギング強化
        logger.info(f"Received request to {request.path} with method {request.method}")
        
        # Get configuration
        config = get_config()
        
        # Initialize Firebase repository
        firebase_repo = FirestoreRepository(
            project_id=config.firebase.project_id,
            credentials_path=config.firebase.credentials_path
        )
        
        # Initialize services
        attendance_service = AttendanceService(firebase_repo)
        monthly_summary_service = MonthlySummaryService(firebase_repo)
        status_service = StatusService(firebase_repo)
        warning_service = WarningService(firebase_repo)
        
        # カスタムOAuthハンドラーの初期化
        custom_oauth_handler = CustomOAuthHandler(
            client_id=config.slack.client_id,
            client_secret=config.slack.client_secret,
            db=firestore.client()
        )
        
        # Setup OAuth with Firestore-based stores
        # OAuthSettingsでinstall_path, redirect_uri_path, success_url, failure_urlを指定済み
        oauth_settings = setup_oauth_flow(
            client_id=config.slack.client_id,
            client_secret=config.slack.client_secret,
            db=firestore.client()
        )
        
        # Initialize Slack app with OAuth
        app = App(oauth_settings=oauth_settings)
        
        # Register commands
        AttendanceCommands(app, attendance_service)
        SummaryCommands(app, monthly_summary_service)
        StatusCommands(app, status_service)

        # Register events
        app.event("member_joined_channel")(handle_bot_invited_to_channel)
        
        # Initialize handler
        handler = SlackRequestHandler(app)
        
        path = request.path
        method = request.method
        
        logger.info(f"Processing path: {path}, method: {method}")

        # OAuth redirect を自前で処理（Bolt のハンドラーを使わない）
        if method == "GET" and path == "/slack/oauth_redirect":
            logger.info("Processing OAuth redirect with custom handler")
            return custom_oauth_handler.handle_oauth_redirect(request)

        # 成功・失敗時のURLはSlack BoltがOAuth完了後にリダイレクトする。
        # ここでは静的なページを返すのみで、handler.handle()を呼ばない。
        if method == "GET" and path == "/slack/oauth_success":
            # インストール成功後の静的メッセージを表示
            logger.info("Returning OAuth success page")
            return Response(
                "<html><body><h1>インストールが完了しました！</h1>"
                "<p>このページを閉じ、Slackワークスペースでボットをお使いください。</p></body></html>",
                status=200,
                mimetype='text/html'
            )
        
        if method == "GET" and path == "/slack/oauth_failure":
            error = request.args.get("error", "不明なエラー")
            logger.error(f"OAuth failure: {error}")
            # インストール失敗時の静的メッセージを表示
            return Response(
                f"<html><body><h1>インストールに失敗しました</h1>"
                f"<p>エラー: {error}</p>"
                f"<p><a href='/slack/install'>再度インストールを試みる</a></p></body></html>",
                status=400,
                mimetype='text/html'
            )

        # それ以外のURLはSlack Boltに処理を委譲
        logger.info(f"Delegating to Bolt handler: {path}")
        return handler.handle(request)
        
    except Exception as e:
        logger.error(f"Error in create_slack_bot_function: {str(e)}", exc_info=True)
        return Response(
            json.dumps({
                "error": "Internal Server Error",
                "message": str(e)
            }),
            status=500,
            mimetype='application/json'
        )