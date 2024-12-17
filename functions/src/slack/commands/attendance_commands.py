from typing import Callable
from slack_bolt import App

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

    def _handle_punch_in(self, ack, command, say):
        """出勤コマンドの処理"""
        ack()
        
        success, message, time = self.attendance_service.punch_in(
            user_id=command["user_id"],
            user_name=command["user_name"]
        )

        if success:
            blocks = MessageBuilder.create_punch_in_message(
                username=command["user_name"],
                time=time
            )
        else:
            blocks = MessageBuilder.create_error_message(message)

        say(
            blocks=blocks,
            channel=command["channel_id"]
        )

    def _handle_punch_out(self, ack, command, say):
        """退勤コマンドの処理"""
        ack()
        
        success, message, attendance = self.attendance_service.punch_out(
            user_id=command["user_id"]
        )

        if success:
            blocks = MessageBuilder.create_punch_out_message(
                username=command["user_name"],
                time=attendance.end_time,
                working_time=attendance.get_working_time(),
                total_break_time=attendance.get_total_break_time()
            )
        else:
            blocks = MessageBuilder.create_error_message(message)

        say(
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
            blocks = MessageBuilder.create_break_start_message(
                username=command["user_name"],
                time=time
            )
        else:
            blocks = MessageBuilder.create_error_message(message)

        say(
            blocks=blocks,
            channel=command["channel_id"]
        )

    def _handle_break_end(self, ack, command, say):
        """休憩終了コマンドの処理"""
        ack()
        
        success, message, result = self.attendance_service.end_break(
            user_id=command["user_id"]
        )

        if success:
            time, duration = result
            blocks = MessageBuilder.create_break_end_message(
                username=command["user_name"],
                time=time,
                duration=duration
            )
        else:
            blocks = MessageBuilder.create_error_message(message)

        say(
            blocks=blocks,
            channel=command["channel_id"]
        )