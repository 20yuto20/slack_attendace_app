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
        
    @staticmethod
    def create_employee_status_message(employee_statuses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        従業員の勤怠状況一覧メッセージを作成
        
        Args:
            employee_statuses: 従業員の勤怠状況のリスト
            
        Returns:
            List[Dict[str, Any]]: Slackブロックメッセージ
        """
        if not employee_statuses:
            return [{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "現在、出勤中の従業員はいません。"
                }
            }]
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "👥 従業員勤怠状況",
                    "emoji": True
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*現在の時刻:* {MessageBuilder.format_time(datetime.now())}"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]
        
        # 従業員ごとのステータスブロックを追加
        for status in employee_statuses:
            # 状態に応じたアイコンとテキスト
            status_emoji = "☕️" if status["status"] == "on_break" else "💼"
            status_text = "休憩中" if status["status"] == "on_break" else "業務中"
            
            # 時間表示
            working_time = MessageBuilder.format_duration(status["working_duration"])
            
            # 休憩時間の表示（休憩中の場合）
            break_info = ""
            if status["status"] == "on_break" and status["break_duration"]:
                break_time = MessageBuilder.format_duration(status["break_duration"])
                break_info = f"• *現在の休憩時間:* {break_time}\n"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<@{status['user_id']}>* {status_emoji} {status_text}\n"
                           f"• *勤務開始:* {MessageBuilder.format_time(status['start_time'])}\n"
                           f"• *経過時間:* {working_time}\n"
                           f"{break_info}"
                           f"• *休憩合計:* {MessageBuilder.format_duration(status['total_break_time'])}"
                }
            })
            
            blocks.append({
                "type": "divider"
            })
        
        return blocks
    
    @staticmethod
    def create_my_status_message(user_name: str, status: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        自分自身の勤怠状況メッセージを作成
        
        Args:
            status: 従業員の勤怠状況
            
        Returns:
            List[Dict[str, Any]]: Slackブロックメッセージ
        """
        # 状態に応じたアイコンとテキスト
        status_emoji = "☕️" if status["status"] == "on_break" else "💼"
        status_text = "休憩中" if status["status"] == "on_break" else "業務中"
        
        # 時間表示
        working_time = MessageBuilder.format_duration(status["working_duration"])
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{user_name}さんの勤怠状況 {status_emoji}",
                    "emoji": True
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*現在の状態:*\n{status_text}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*勤務開始時刻:*\n{MessageBuilder.format_time(status['start_time'])}"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*経過時間:*\n{working_time}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*休憩合計:*\n{MessageBuilder.format_duration(status['total_break_time'])}"
                    }
                ]
            }
        ]
        
        # 休憩中の場合は休憩時間も表示
        if status["status"] == "on_break" and status["break_duration"]:
            blocks.append({
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*現在の休憩時間:*\n{MessageBuilder.format_duration(status['break_duration'])}"
                    }
                ]
            })
        
        return blocks