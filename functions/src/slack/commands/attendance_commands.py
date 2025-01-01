from typing import Callable, List
from slack_bolt import App
from slack_sdk import WebClient

from src.services.attendance_service import AttendanceService
from src.slack.message_builder import MessageBuilder
from src.models.attendance import Attendance

class AttendanceCommands:
    def __init__(self, app: App, attendance_service: AttendanceService):
        self.app = app
        self.attendance_service = attendance_service
        self._register_commands()
        self._register_view_submissions()

    def _register_commands(self) -> None:
        """すべてのコマンドを登録"""
        self._register_command("/punch_in", self._handle_punch_in)
        # /punch_out は即退勤ではなく、モーダルを開くよう修正
        self._register_command("/punch_out", self._handle_punch_out_modal_trigger)
        self._register_command("/break_begin", self._handle_break_begin)
        self._register_command("/break_end", self._handle_break_end)

    def _register_view_submissions(self):
        """
        モーダル（退勤報告用）からの view_submission をハンドル
        callback_id を "punch_out_report_modal" とする
        """
        @self.app.view("punch_out_report_modal")
        def handle_punch_out_modal_submission(ack, body, view, client, logger, say, command=None):
            """
            退勤モーダル送信時の処理:
            1. フォーム入力情報を取得
            2. 退勤処理
            3. Firestore に業務情報を保存
            4. 選択されたチャンネルに業務報告を投稿
            5. コマンド実行チャンネルに退勤メッセージを送信
            """
            ack()

            # Slack が view_submission を発火する際、commandが必ずしも body に含まれるとは限りません。
            # もし command を受け取りたい場合は、private_metadata 等にチャンネル情報をセットしておく方法が一般的です。
            # ここでは簡易的に private_metadata に格納されていると仮定して処理を進めます。
            try:
                metadata = view.get("private_metadata", "{}")
            except Exception as e:
                metadata = "{}"
                logger.info(f"No private_metadata found: {e}")

            import json
            try:
                meta_dict = json.loads(metadata)
            except:
                meta_dict = {}

            fallback_channel_id = meta_dict.get("channel_id", "")  # モーダル開いた時点でのチャンネルID

            user_id = body["user"]["id"]
            user_name = body["user"]["name"]

            # --- [1] フォーム入力情報を取得 ---
            work_description = view["state"]["values"]["work_description_block"]["work_description_input"]["value"]
            work_progress = view["state"]["values"]["work_progress_block"]["work_progress_input"]["value"]

            channel_id_selected = view["state"]["values"]["report_channel_block"]["report_channel_input"]["selected_conversation"]
            mention_users_selected = view["state"]["values"]["mention_users_block"]["mention_users_input"].get("selected_users", [])

            # --- [2] 退勤処理 ---
            success, message, attendance = self.attendance_service.punch_out(
                user_id=user_id
            )

            if not success or not attendance:
                # 退勤に失敗した場合はエラーを DM 等に送信して終了
                client.chat_postMessage(channel=user_id, text=f"退勤処理に失敗しました: {message}")
                return

            # --- [3] Firestore に業務情報を保存 ---
            attendance.work_description = work_description
            attendance.work_progress = work_progress
            attendance.report_channel_id = channel_id_selected
            attendance.mention_user_ids = mention_users_selected

            # 退勤時に update_attendance は punch_out 内部で完了しているが、
            # 業務情報を上書きするために再度 update する
            self.attendance_service.repository.update_attendance(attendance)

            # --- [4] 選択されたチャンネルに業務報告を投稿 ---
            if channel_id_selected:
                # 実働時間・休憩時間の算出
                working_time = attendance.get_working_time()
                break_time = attendance.get_total_break_time()

                # メンション文字列
                mention_text = ""
                if mention_users_selected:
                    mention_text = " ".join([f"<@{uid}>" for uid in mention_users_selected])

                # Blocks 形式で見やすく表示
                # Markdownで整形した各項目を表示
                report_blocks = [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "本日の業務報告",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*報告者:*\n<@{user_id}>"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*実働時間:*\n{MessageBuilder.format_duration(working_time)}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*休憩時間:*\n{MessageBuilder.format_duration(break_time)}"
                            }
                        ]
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*業務概要:*\n{work_description}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*進捗:*\n{work_progress}"
                            }
                        ]
                    }
                ]

                # 投稿するテキスト（fallback用）
                fallback_text = (
                    f"報告者: <@{user_id}>\n"
                    f"実働時間: {MessageBuilder.format_duration(working_time)}\n"
                    f"休憩時間: {MessageBuilder.format_duration(break_time)}\n"
                    f"業務概要:\n{work_description}\n"
                    f"進捗:\n{work_progress}"
                )
                # メンションを冒頭に追加する場合
                if mention_text:
                    fallback_text = mention_text + "\n" + fallback_text

                try:
                    client.chat_postMessage(
                        channel=channel_id_selected,
                        text=fallback_text,
                        blocks=report_blocks,
                        mrkdwn=True
                    )
                except Exception as e:
                    client.chat_postMessage(
                        channel=user_id,
                        text=f"業務報告の投稿に失敗しました: {str(e)}"
                    )

            # --- [5] コマンド実行チャンネルに退勤メッセージを送信 ---
            blocks = MessageBuilder.create_punch_out_message(
                username=user_name,
                time=attendance.end_time,
                working_time=attendance.get_working_time(),
                total_break_time=attendance.get_total_break_time()
            )
            self._handle_slack_status(user_id=user_id, text="", emoji="")
            final_channel_id = fallback_channel_id
            if command and "channel_id" in command:
                final_channel_id = command["channel_id"]

            client.chat_postMessage(
                channel=final_channel_id,
                text="退勤",
                blocks=blocks
            )

    def _register_command(self, command: str, handler: Callable) -> None:
        """個別のコマンドを登録"""
        self.app.command(command)(handler)

    def _handle_slack_status(self, user_id: str, text: str, emoji: str):
        """
        Slackのステータスを更新する。
        - ただし Bot Token は使えないため、ユーザートークンを利用する。
        """
        try:
            auth_test = self.app.client.auth_test()
            team_id = auth_test.get("team_id")
            enterprise_id = auth_test.get("enterprise_id", None)

            installation = self.app.installation_store.find_installation(
                team_id=team_id,
                enterprise_id=enterprise_id,
                user_id=user_id
            )

            if not installation or not installation.user_token:
                print(f"[WARNING] Installation not found or user_token not found for user {user_id}")
                return
            
            user_client = WebClient(token=installation.user_token)
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

        say(
            text="出勤",
            blocks=blocks,
            channel=command["channel_id"]
        )

    def _handle_punch_out_modal_trigger(self, ack, command, client, say):
        """
        /punch_out を入力したときにモーダルを開く
        """
        ack()

        import json
        private_metadata = json.dumps({
            "channel_id": command["channel_id"]
        })

        modal_view = {
            "type": "modal",
            "callback_id": "punch_out_report_modal",
            "title": {
                "type": "plain_text",
                "text": "退勤報告"
            },
            "submit": {
                "type": "plain_text",
                "text": "退勤"
            },
            "close": {
                "type": "plain_text",
                "text": "キャンセル"
            },
            "private_metadata": private_metadata,
            "blocks": [
                {
                    "type": "input",
                    "block_id": "work_description_block",
                    "label": {
                        "type": "plain_text",
                        "text": "本日の業務内容"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "work_description_input",
                        "multiline": True
                    }
                },
                {
                    "type": "input",
                    "block_id": "work_progress_block",
                    "label": {
                        "type": "plain_text",
                        "text": "詳しい進捗"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "work_progress_input",
                        "multiline": True
                    }
                },
                {
                    "type": "input",
                    "block_id": "report_channel_block",
                    "label": {
                        "type": "plain_text",
                        "text": "報告先チャンネル"
                    },
                    "element": {
                        "type": "conversations_select",
                        "action_id": "report_channel_input",
                        "default_to_current_conversation": False,
                        "response_url_enabled": False
                    }
                },
                {
                    "type": "input",
                    "block_id": "mention_users_block",
                    "optional": True,
                    "label": {
                        "type": "plain_text",
                        "text": "メンションするユーザー（任意）"
                    },
                    "element": {
                        "type": "multi_users_select",
                        "action_id": "mention_users_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "メンションしたいユーザーを選択"
                        }
                    }
                }
            ]
        }

        client.views_open(
            trigger_id=command["trigger_id"],
            view=modal_view
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
