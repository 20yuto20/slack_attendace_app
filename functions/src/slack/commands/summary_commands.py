from datetime import datetime
from typing import Dict, Any, List

from slack_bolt import App
# from slack_sdk import WebClient

from ...services.monthly_summary_service import MonthlySummaryService
from ..message_builder import MessageBuilder

class SummaryCommands:
    def __init__(self, app: App, summary_service: MonthlySummaryService):
        self.app = app
        self.summary_service = summary_service
        self._register_commands()

    def _register_commands(self) -> None:
        """
        すべてのコマンドとビュー（モーダル）サブミッション、アクションを登録
        """
        # /summary コマンド
        self.app.command("/summary")(self._handle_summary)

        # 新規追加: /help コマンド
        self.app.command("/help")(self._handle_help)

        # モーダルの submit アクション
        @self.app.view("summary_modal")
        def _handle_summary_modal_submission(ack, body, view, client, logger):
            """
            モーダル送信時（「表示」ボタン押下時）の処理
            1. 年・月・選択チャンネルを取得
            2. 選択したチャンネルにサマリーを投稿
            """
            ack()

            user_id = body["user"]["id"]
            user_name = body["user"]["name"]

            # モーダル上の values を取得
            year_str = view["state"]["values"]["year_block"]["year_select"]["selected_option"]["value"]
            month_str = view["state"]["values"]["month_block"]["month_select"]["selected_option"]["value"]
            channel_list = view["state"]["values"]["channel_block"]["channel_select"]["selected_conversations"]

            year = int(year_str)
            month = int(month_str)

            # 取得した年・月で月次サマリーを作成
            summary = self.summary_service.get_monthly_summary(
                user_id=user_id,
                year=year,
                month=month
            )

            # 表示用のブロックを生成
            blocks = MessageBuilder.create_monthly_summary_message(
                username=user_name,
                summary=summary
            )

            # 選択されたチャンネルそれぞれに投稿
            if channel_list:
                for ch in channel_list:
                    try:
                        client.chat_postMessage(
                            channel=ch,
                            text=f"{year}年{month}月の勤怠サマリー",
                            blocks=blocks
                        )
                    except Exception as e:
                        logger.error(f"Failed to post summary to channel {ch}: {e}")

        # CSVダウンロードのボタンアクション
        self.app.action("download_csv")(self._handle_csv_download)

    def _handle_summary(self, ack, command, client):
        """
        /summary コマンド:
        1. モーダルを開く (年・月・チャンネル選択 + 「表示」ボタン)
        """
        ack()

        trigger_id = command["trigger_id"]

        # モーダルのレイアウト定義
        modal_view = {
            "type": "modal",
            "callback_id": "summary_modal",
            "title": {
                "type": "plain_text",
                "text": "勤怠サマリー表示"
            },
            "submit": {
                "type": "plain_text",
                "text": "表示"
            },
            "close": {
                "type": "plain_text",
                "text": "キャンセル"
            },
            "blocks": [
                {
                    "type": "section",
                    "block_id": "year_block",
                    "text": {
                        "type": "mrkdwn",
                        "text": "年を選択してください"
                    },
                    "accessory": {
                        "type": "static_select",
                        "action_id": "year_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "年"
                        },
                        "options": self._build_year_options()
                    }
                },
                {
                    "type": "section",
                    "block_id": "month_block",
                    "text": {
                        "type": "mrkdwn",
                        "text": "月を選択してください"
                    },
                    "accessory": {
                        "type": "static_select",
                        "action_id": "month_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "月"
                        },
                        "options": self._build_month_options()
                    }
                },
                {
                    "type": "input",
                    "block_id": "channel_block",
                    "element": {
                        "type": "multi_conversations_select",
                        "action_id": "channel_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "投稿先チャンネルを選択"
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "サマリーを表示するチャンネル"
                    }
                }
            ]
        }

        # モーダルを開く
        client.views_open(
            trigger_id=trigger_id,
            view=modal_view
        )

    def _handle_help(self, ack, command, say):
        """
        新規追加: /help コマンドの処理
        以前の handle_mention_help と同じメッセージを表示
        """
        ack()
        help_message = (
            "▼ 以下のコマンドをご利用いただけます。\n\n"
            "• `/punch_in`: 出勤\n"
            "• `/punch_out`: 退勤\n"
            "• `/break_begin`: 休憩開始\n"
            "• `/break_end`: 休憩終了\n"
            "• `/summary`: 勤怠サマリー\n"
            "• `/help`: 使い方ガイドの表示\n\n"
            "こちらのガイドサイトにも詳しい使い方が掲載されています。\n"
            "<https://aerial-lentil-c95.notion.site/bot-164d7101a27680d98fbae0385153a637>\n\n"
            "不明点があればお気軽にお問い合わせください！"
        )
        # /help コマンドを打ったチャンネルにヘルプを投稿
        say(text=help_message, channel=command["channel_id"])

    def _handle_csv_download(self, ack, body, client):
        """
        CSVダウンロードボタンの処理:
        1. ボタンの value から年・月を取得
        2. CSVを生成してアップロード
        """
        ack()
    
        year_month = body["actions"][0]["value"]
        year, month = map(int, year_month.split("-"))
    
        user_id = body["user"]["id"]
        user_name = body["user"]["name"]

        filename, csv_content = self.summary_service.generate_csv(
            user_id=user_id,
            user_name=user_name,
            year=year,
            month=month
        )
    
        try:
            response = client.files_upload_v2(
                channel=body["channel"]["id"],
                filename=filename,
                content=csv_content,
                title=f"{year}年{month}月の勤怠記録",
                initial_comment=f"{year}年{month}月の勤怠記録をCSVでダウンロードしました。"
            )
        
            if not response["ok"]:
                client.chat_postMessage(
                    channel=body["channel"]["id"],
                    text=f"CSVファイルのアップロードに失敗しました：{response.get('error', '不明なエラー')}"
                )
        except Exception as e:
            client.chat_postMessage(
                channel=body["channel"]["id"],
                text=f"CSVファイルのアップロードに失敗しました：{str(e)}"
            )

    def _build_year_options(self) -> List[Dict[str, Any]]:
        """
        2023年から現在の+1年くらいまで、あるいは固定範囲を想定して
        年を選択できる static_select の options を構築
        """
        year_options = []
        for y in range(2022, 2027):
            year_options.append({
                "text": {
                    "type": "plain_text",
                    "text": f"{y}年"
                },
                "value": str(y)
            })
        return year_options

    def _build_month_options(self) -> List[Dict[str, Any]]:
        """
        1〜12月を選択できる static_select の options
        """
        month_options = []
        for m in range(1, 13):
            month_options.append({
                "text": {
                    "type": "plain_text",
                    "text": f"{m}月"
                },
                "value": str(m)
            })
        return month_options
