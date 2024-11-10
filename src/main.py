import asyncio
from flask import Flask, request
import functions_framework
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from src.config import init_config
from src.repositories.firestore_repository import FirestoreRepository
from src.services.attendance_service import AttendanceService
from src.services.monthly_summary_service import MonthlySummaryService
from src.slack.app import SlackApp

# Configuration
config = init_config()

print("Initializing services...")

# Initialize repositories
firestore_repo = FirestoreRepository(
    project_id=config.firebase.project_id,
    credentials_path=config.firebase.credentials_path
)

# Initialize services
attendance_service = AttendanceService(firestore_repo)
monthly_summary_service = MonthlySummaryService(firestore_repo)  # 追加

print("Initializing Slack app...")

# Initialize Slack app
slack_app = SlackApp(
    bot_token=config.slack.bot_token,
    signing_secret=config.slack.signing_secret,
    app_token=config.slack.app_token,
    attendance_service=attendance_service,
    monthly_summary_service=monthly_summary_service  # 追加
)

app = Flask(__name__)
handler = slack_app.get_handler()

@functions_framework.http
def slack_bot(request):
    """Cloud Functions用のエントリーポイント"""
    if request.method == "POST":
        # Slackからのリクエストを処理
        return handler.handle(request)
    return "Method not allowed", 405

async def start_socket_mode():
    """Socket Modeハンドラーの起動"""
    try:
        app_handler = AsyncSocketModeHandler(
            app=slack_app.get_app(),
            app_token=config.slack.app_token
        )
        await app_handler.start_async()
    except Exception as e:
        print(f"Error starting socket mode: {e}")
        raise

if __name__ == "__main__":
    print("Starting socket mode...")
    # ローカル開発用
    # Socket Modeの場合
    asyncio.run(start_socket_mode())