from datetime import datetime, timedelta
import calendar
import pytz

from ..config import get_config

def get_current_time() -> datetime:
    """現在時刻を設定されたタイムゾーンで取得"""
    config = get_config()
    timezone = pytz.timezone(config.application.timezone)
    return datetime.now(timezone)

def get_start_of_month(year: int, month: int) -> datetime:
    """月初日の0時0分を取得"""
    config = get_config()
    timezone = pytz.timezone(config.application.timezone)
    return datetime(year, month, 1, 0, 0, 0, tzinfo=timezone)

def get_end_of_month(year: int, month: int) -> datetime:
    """月末日の23時59分59秒を取得"""
    config = get_config()
    timezone = pytz.timezone(config.application.timezone)
    
    # 月末日を取得
    _, last_day = calendar.monthrange(year, month)
    
    return datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone)

def get_week_number(date: datetime) -> int:
    """日付から週番号を取得（1-5）"""
    return (date.day - 1) // 7 + 1