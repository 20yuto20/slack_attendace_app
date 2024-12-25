from datetime import datetime
from typing import Dict, Any, List

from slack_bolt import App

from ...services.monthly_summary_service import MonthlySummaryService
from ..message_builder import MessageBuilder

class SummaryCommands:
    def __init__(self, app: App, summary_service: MonthlySummaryService):
        self.app = app
        self.summary_service = summary_service
        self._register_commands()

    def _register_commands(self) -> None:
        """すべてのコマンドを登録"""
        self.app.command("/summary")(self._handle_summary)
        self.app.action("select_year")(self._handle_year_selection)
        self.app.action("select_month")(self._handle_month_selection)
        self.app.action("download_csv")(self._handle_csv_download)

    def _handle_summary(self, ack, body, say):
        """サマリーコマンドの処理"""
        ack()
        
        current_date = datetime.now()
        # 月選択用のブロックを生成するメソッドを呼び出し
        blocks = self._create_month_selector_blocks(current_date.year)
        
        say(
            blocks=blocks,
            channel=body["channel_id"]
        )
    
    def _handle_year_selection(self, ack, body, say):
        """年選択の処理"""
        ack()
        
        selected_value = body["actions"][0]["selected_option"]["value"]
        year = int(selected_value)
        
        blocks = self._create_month_selector_blocks(year)
        say(
            blocks=blocks,
            channel=body["channel_id"]
        )

    def _handle_month_selection(self, ack, body, say):
        """月選択の処理"""
        ack()
        
        selected_value = body["actions"][0]["selected_option"]["value"]
        year, month = map(int, selected_value.split("-"))
        
        summary = self.summary_service.get_monthly_summary(
            user_id=body["user"]["id"],
            year=year,
            month=month
        )
        
        blocks = MessageBuilder.create_monthly_summary_message(
            username=body["user"]["name"],
            summary=summary
        )
        
        say(
            blocks=blocks,
            channel=body["channel"]["id"]
        )

    def _handle_csv_download(self, ack, body, client):
        """CSVダウンロードの処理"""
        ack()
    
        year_month = body["actions"][0]["value"]
        year, month = map(int, year_month.split("-"))
    
        filename, csv_content = self.summary_service.generate_csv(
            user_id=body["user"]["id"],
            user_name=body["user"]["name"],
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

    def _create_month_selector_blocks(self, current_year: int) -> List[Dict[str, Any]]:
        """
        年と月を選択できるブロックを返すメソッド。
        年は2024年から現在の年まで、月は1月から12月まで選択可能。
        """
        # 年の選択肢を作成
        year_options = []
        for y in range(2024, current_year + 1):
            year_options.append({
                "text": {
                    "type": "plain_text",
                    "text": f"{y}年"
                },
                "value": str(y)
            })

        # 月の選択肢を作成
        month_options = []
        for m in range(1, 13):
            month_options.append({
                "text": {
                    "type": "plain_text",
                    "text": f"{m}月"
                },
                "value": f"{current_year}-{m}"
            })

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "年を選択してください"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "年を選択"
                    },
                    "options": year_options,
                    "action_id": "select_year"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "月を選択してください"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "月を選択"
                    },
                    "options": month_options,
                    "action_id": "select_month"
                }
            }
        ]
        return blocks