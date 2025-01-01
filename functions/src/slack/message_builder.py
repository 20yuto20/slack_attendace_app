from datetime import datetime
from typing import List, Dict, Any

class MessageBuilder:
    @staticmethod
    def format_time(dt: datetime) -> str:
        """時刻を見やすい形式にフォーマット"""
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def format_duration(minutes: float) -> str:
        """時間を時間と分の形式にフォーマット"""
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        if hours > 0:
            return f"{hours}時間{mins}分"
        return f"{mins}分"

    @staticmethod
    def create_punch_in_message(username: str, time: datetime) -> List[Dict[str, Any]]:
        """出勤メッセージを作成"""
        return [
            {
                "type": "divider"
            },
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "☀️ 出勤記録",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*従業員:*\n{username}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*出勤時刻:*\n{MessageBuilder.format_time(time)}"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "今日も一日頑張りましょう！ 👍"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]

    @staticmethod
    def create_punch_out_message(username: str, time: datetime, working_time: float, total_break_time: float) -> List[Dict[str, Any]]:
        """退勤メッセージを作成"""
        return [
            {
                "type": "divider"
            },
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🌙 退勤記録",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*従業員:*\n{username}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*退勤時刻:*\n{MessageBuilder.format_time(time)}"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*実働時間:*\n{MessageBuilder.format_duration(working_time)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*休憩時間:*\n{MessageBuilder.format_duration(total_break_time)}"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "お疲れ様でした！ 🌟"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]

    @staticmethod
    def create_break_start_message(username: str, time: datetime) -> List[Dict[str, Any]]:
        """休憩開始メッセージを作成"""
        return [
            {
                "type": "divider"
            },
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "☕️ 休憩開始",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*従業員:*\n{username}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*開始時刻:*\n{MessageBuilder.format_time(time)}"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "ゆっくり休憩してください 🍵"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]

    @staticmethod
    def create_break_end_message(username: str, time: datetime, duration: float) -> List[Dict[str, Any]]:
        """休憩終了メッセージを作成"""
        return [
            {
                "type": "divider"
            },
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🔙 休憩終了",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*従業員:*\n{username}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*終了時刻:*\n{MessageBuilder.format_time(time)}"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*休憩時間:*\n{MessageBuilder.format_duration(duration)}"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "それでは、仕事に戻りましょう！ 💪"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]

    @staticmethod
    def create_error_message(error_message: str) -> List[Dict[str, Any]]:
        """エラーメッセージを作成"""
        return [
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"⚠️ *エラー*: {error_message}"
                }
            },
            {
                "type": "divider"
            }
        ]
    
    @staticmethod
    def create_monthly_summary_message(username: str, summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """月次サマリーメッセージを作成"""
        
        if summary['total_working_time'] == 0:
            return [
                {
                    "type": "divider"
                },
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📊 {summary['year']}年{summary['month']}月の勤怠サマリー",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{summary['year']}年{summary['month']}月は稼働がありませんでした。"
                    }
                },
                {
                    "type": "divider"
                }
            ]

        blocks = [
            {
                "type": "divider"
            },
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 {summary['year']}年{summary['month']}月の勤怠サマリー",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*従業員:*\n{username}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*月間合計勤務時間:*\n{MessageBuilder.format_duration(summary['total_working_time'])}"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]

        # 週次サマリーを追加
        weekly_fields = []
        for week, total in summary['weekly_totals'].items():
            weekly_fields.append({
                "type": "mrkdwn",
                "text": f"*第{week}週:*\n{MessageBuilder.format_duration(total)}"
            })

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*週次サマリー*"
            }
        })

        blocks.append({
            "type": "section",
            "fields": weekly_fields
        })

        # CSVダウンロードボタンを追加
        blocks.extend([
            {
                "type": "divider"
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "CSVでダウンロード",
                            "emoji": True
                        },
                        "value": f"{summary['year']}-{summary['month']}",
                        "action_id": "download_csv",
                        "style": "primary"
                    }
                ]
            }
        ])

        return blocks