from typing import Callable, List
from slack_bolt import App
from slack_sdk import WebClient
# from slack_bolt.context.respond import Respond
# from slack_bolt.context.say import Say
# from slack_bolt.adapter.aws_lambda import SlackRequestHandler

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

            # private_metadata は JSON 形式で格納している場合が多いので、必要に応じて parse する
            import json
            try:
                meta_dict = json.loads(metadata)
            except:
                meta_dict = {}

            # ここでは /punch_out コマンドを打ったチャンネルを private_metadata["channel_id"] に入れている想定
            fallback_channel_id = meta_dict.get("channel_id", "")  # モーダル開いた時点で記憶しているチャンネルID

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
                report_text = f"*本日の業務報告*\n- 業務概要: {work_description}\n- 進捗: {work_progress}"
                if mention_users_selected:
                    # メンション文字列を組み立てる
                    mentions = " ".join([f"<@{uid}>" for uid in mention_users_selected])
                    report_text = f"{mentions}\n" + report_text

                try:
                    client.chat_postMessage(
                        channel=channel_id_selected,
                        text=report_text
                    )
                except Exception as e:
                    client.chat_postMessage(
                        channel=user_id,
                        text=f"業務報告の投稿に失敗しました: {str(e)}"
                    )

            # --- [5] コマンド実行チャンネルに退勤メッセージを送信 ---
            # 退勤メッセージ用のブロックを作成
            blocks = MessageBuilder.create_punch_out_message(
                username=user_name,
                time=attendance.end_time,
                working_time=attendance.get_working_time(),
                total_break_time=attendance.get_total_break_time()
            )
            # Slackのステータスをクリア
            self._handle_slack_status(user_id=user_id, text="", emoji="")
            # ここを修正: command["channel_id"] が使えるかどうかの可用性に注意
            # 一般的には private_metadata 経由でチャンネルIDを取得するので fallback_channel_id を使う
            # 修正要望に忠実に「command["channel_id"]」を利用したい場合、例外処理を入れます。
            final_channel_id = fallback_channel_id
            # 万が一 command["channel_id"] が使える場合のサンプル
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

        # private_metadata にコマンド発行チャンネルIDを保存しておく
        import json
        private_metadata = json.dumps({
            "channel_id": command["channel_id"]
        })

        # モーダルを作成
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
            # 上記で作成した metadata をセット
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
                    # channels_select -> conversations_select に変更
                    # private channel も選べるよう "include_private_channels": True 相当が必要
                    # Slack Bolt Blocksではデフォルトで private channel を含むようになっていますが
                    # オプション: filter に { "include": ["private"] } 等は 2023年時点未サポート
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

        # モーダルを開く
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
