from typing import Callable
from slack_bolt import App
from slack_sdk import WebClient

from src.services.attendance_service import AttendanceService
from src.slack.message_builder import MessageBuilder

class AttendanceCommands:
    def __init__(self, app: App, attendance_service: AttendanceService):
        self.app = app
        self.attendance_service = attendance_service
        self._register_commands()

    def _register_commands(self) -> None:
        """すべてのコマンドを登録"""
        self._register_command("/punch_in", self._handle_punch_in)
        self._register_command("/punch_out", self._handle_punch_out)
        self._register_command("/break_begin", self._handle_break_begin)
        self._register_command("/break_end", self._handle_break_end)

    def _register_command(self, command: str, handler: Callable) -> None:
        """個別のコマンドを登録"""
        self.app.command(command)(handler)

    def _handle_slack_status(self, user_id: str, text: str, emoji: str):
        """
        Slackのステータスを更新する。
        - ただし Bot Token は使えないため、ユーザートークンを利用する。
        """
        try:
            # Botトークンで auth_test() を呼ぶと "As `installation_store` or `authorize` has been used... " という警告が出る場合あり
            # ここでは team_id/enterprise_id を取得するために auth_test() を使っていますが、
            # コマンドハンドラ (command["team_id"]) などから取得する方法でもOKです。
            auth_test = self.app.client.auth_test()
            team_id = auth_test.get("team_id")
            enterprise_id = auth_test.get("enterprise_id", None)

            # 修正ポイント: FirestoreInstallationStore では "find_installation" を使う
            installation = self.app.installation_store.find_installation(
                team_id=team_id,
                enterprise_id=enterprise_id,
                user_id=user_id
            )

            if not installation or not installation.user_token:
                print(f"[WARNING] Installation not found or user_token not found for user {user_id}")
                return
            
            # ユーザートークンでクライアントを生成
            user_client = WebClient(token=installation.user_token)

            # users_profile_set (slack_sdk 3.x系) で呼ぶ場合
            user_client.users_profile_set(
                user=user_id,
                profile={
                    "status_text": text,
                    "status_emoji": emoji,
                    "status_expiration": 0
                }
            )
        except Exception as e:
            print(f"Slackのステータス更新に失敗しました: {e}")

    def _handle_punch_in(self, ack, command, say):
        """出勤コマンドの処理"""
        ack()
        
        success, message, time = self.attendance_service.punch_in(
            user_id=command["user_id"],
            user_name=command["user_name"]
        )

        if success:
            # ステータス更新
            self._handle_slack_status(
                user_id=command["user_id"],
                text="業務中",
                emoji=":sunny:"
            )
            blocks = MessageBuilder.create_punch_in_message(
                username=command["user_name"],
                time=time
            )
        else:
            blocks = MessageBuilder.create_error_message(message)

        # text= を指定することで警告が消える
        say(
            text="出勤",
            blocks=blocks,
            channel=command["channel_id"]
        )

    def _handle_punch_out(self, ack, command, say):
        """退勤コマンドの処理"""
        ack()
        
        success, message, attendance = self.attendance_service.punch_out(
            user_id=command["user_id"]
        )

        if success and attendance is not None:
            # ステータス更新
            self._handle_slack_status(
                user_id=command["user_id"],
                text="",
                emoji=""
            )
            blocks = MessageBuilder.create_punch_out_message(
                username=command["user_name"],
                time=attendance.end_time,
                working_time=attendance.get_working_time(),
                total_break_time=attendance.get_total_break_time()
            )
        else:
            blocks = MessageBuilder.create_error_message(message)

        say(
            text="退勤",
            blocks=blocks,
            channel=command["channel_id"]
        )

    def _handle_break_begin(self, ack, command, say):
        """休憩開始コマンドの処理"""
        ack()
        
        success, message, time = self.attendance_service.start_break(
            user_id=command["user_id"]
        )

        if success:
            self._handle_slack_status(
                user_id=command["user_id"],
                text="休憩中",
                emoji=":coffee:"
            )
            blocks = MessageBuilder.create_break_start_message(
                username=command["user_name"],
                time=time
            )
        else:
            blocks = MessageBuilder.create_error_message(message)

        say(
            text="休憩開始",
            blocks=blocks,
            channel=command["channel_id"]
        )

    def _handle_break_end(self, ack, command, say):
        """休憩終了コマンドの処理"""
        ack()
        
        success, message, result = self.attendance_service.end_break(
            user_id=command["user_id"]
        )

        if success and result is not None:
            self._handle_slack_status(
                user_id=command["user_id"],
                text="業務中",
                emoji=":sunny:"
            )
            time, duration = result
            blocks = MessageBuilder.create_break_end_message(
                username=command["user_name"],
                time=time,
                duration=duration
            )
        else:
            blocks = MessageBuilder.create_error_message(message)

        say(
            text="休憩終了",
            blocks=blocks,
            channel=command["channel_id"]
        )
