from typing import List, Dict, Any
from slack_bolt import App

from src.services.status_service import StatusService
from src.slack.message_builder import MessageBuilder
from src.utils.time_utils import get_current_time

class StatusCommands:
    def __init__(self, app: App, status_service: StatusService):
        self.app = app
        self.status_service = status_service
        self._register_commands()
    
    def _register_commands(self) -> None:
        """コマンドを登録"""
        self.app.command("/allstatus")(self._handle_status)
        self.app.command("/mystatus")(self._handle_my_status)
    
    def _handle_status(self, ack, command, say, client):
        """
        /status コマンド - すべてのアクティブな従業員の状態を表示
        """
        ack()
        
        # コマンドを実行したワークスペースのIDを取得
        team_id = command.get("team_id")
        
        # アクティブな従業員の状態を取得（同じワークスペースに限定）
        active_employees = self.status_service.get_active_employees(team_id=team_id)
        
        if not active_employees:
            say("現在、出勤中の従業員はいません。")
            return
        
        # Slackブロックメッセージを構築
        blocks = MessageBuilder.create_employee_status_message(active_employees)
        
        # メッセージを送信
        say(
            text="従業員の勤怠状況",
            blocks=blocks,
            channel=command["channel_id"]
        )
    
    def _handle_my_status(self, ack, command, say, client):
        """
        /mystatus コマンド - 自分自身の現在の状態を表示
        """
        ack()
        
        user_id = command["user_id"]
        user_name = command["user_name"]
        team_id = command.get("team_id")  # ワークスペースIDを取得
        
        # 従業員の状態を取得（同じワークスペースに限定）
        status = self.status_service.get_employee_status(user_id, team_id=team_id)
        
        if not status:
            say(
                text=f"{user_name}さんは現在出勤していません。",
                channel=command["channel_id"]
            )
            return
        
        # Slackブロックメッセージを構築
        blocks = MessageBuilder.create_my_status_message(user_name, status)
        
        # メッセージを送信
        say(
            text="あなたの勤怠状況",
            blocks=blocks,
            channel=command["channel_id"]
        )