from datetime import datetime
from typing import Dict, Any, List

from slack_bolt import App
from slack_bolt.async_app import AsyncApp

from ...services.monthly_summary_service import MonthlySummaryService
from ..message_builder import MessageBuilder

class SummaryCommands:
    def __init__(self, app: AsyncApp, summary_service: MonthlySummaryService):
        self.app = app
        self.summary_service = summary_service
        self._register_commands()

    def _register_commands(self) -> None:
        """すべてのコマンドを登録"""
        self.app.command("/summary")(self._handle_summary)
        self.app.action("select_month")(self._handle_month_selection)
        self.app.action("download_csv")(self._handle_csv_download)

    async def _handle_summary(self, ack, body, say):
        """サマリーコマンドの処理"""
        await ack()
        
        current_date = datetime.now()
        blocks = self._create_month_selector_blocks(current_date.year)
        
        await say(
            blocks=blocks,
            channel=body["channel_id"]
        )

    async def _handle_month_selection(self, ack, body, say):
        """月選択の処理"""
        await ack()
        
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
        
        await say(
            blocks=blocks,
            channel=body["channel"]["id"]
        )

    async def _handle_csv_download(self, ack, body, client):
        """CSVダウンロードの処理"""
        await ack()
    
        # 選択された年月を取得
        year_month = body["actions"][0]["value"]
        year, month = map(int, year_month.split("-"))
    
        # CSVを生成
        filename, csv_content = self.summary_service.generate_csv(
            user_id=body["user"]["id"],
            user_name=body["user"]["name"],
            year=year,
            month=month
        )
    
        try:
            # files_upload_v2を使用してファイルをアップロード
            response = await client.files_upload_v2(
                channel=body["channel"]["id"],
                filename=filename,
                content=csv_content,
                title=f"{year}年{month}月の勤怠記録",
                initial_comment=f"{year}年{month}月の勤怠記録をCSVでダウンロードしました。"
            )
        
            if not response["ok"]:
                # エラーメッセージを表示
                await client.chat_postMessage(
                    channel=body["channel"]["id"],
                    text=f"CSVファイルのアップロードに失敗しました：{response.get('error', '不明なエラー')}"
                )
        except Exception as e:
            # エラーメッセージを表示
            await client.chat_postMessage(
                channel=body["channel"]["id"],
                text=f"CSVファイルのアップロードに失敗しました：{str(e)}"
            )

    def _create_month_selector_blocks(self, year: int) -> List[Dict[str, Any]]:
        """月選択用のブロックを作成"""
        months = []
        for month in range(1, 13):
            months.append({
                "text": {
                    "type": "plain_text",
                    "text": f"{year}年{month}月"
                },
                "value": f"{year}-{month}"
            })

        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "📊 *勤怠サマリー*\n確認したい月を選択してください。"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "static_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "月を選択",
                            "emoji": True
                        },
                        "options": months,
                        "action_id": "select_month"
                    }
                ]
            }
        ]