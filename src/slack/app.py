from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.flask import SlackRequestHandler

from src.services.attendance_service import AttendanceService
from src.services.monthly_summary_service import MonthlySummaryService  # 追加
from src.slack.commands.attendance_commands import AttendanceCommands
from src.slack.commands.summary_commands import SummaryCommands  # 追加

class SlackApp:
    def __init__(
        self,
        bot_token: str,
        signing_secret: str,
        app_token: str,
        attendance_service: AttendanceService,
        monthly_summary_service: MonthlySummaryService
    ):
        self.app = AsyncApp(
            token=bot_token,
            signing_secret=signing_secret
        )
        self.handler = SlackRequestHandler(self.app)
        self.app_token = app_token
        
        # コマンドの登録
        AttendanceCommands(self.app, attendance_service)
        SummaryCommands(self.app, monthly_summary_service)

    def get_handler(self) -> SlackRequestHandler:
        return self.handler

    def get_app(self) -> AsyncApp:
        return self.app