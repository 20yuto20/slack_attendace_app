from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class Attendance:
    """出勤記録のスキーマ定義"""
    user_id: str
    user_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_break_time: float = 0.0  # 休憩時間の合計（分）

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "start_time": start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_break_time": self.total_break_time
        }

@dataclass
class BreakTime:
    """休憩時間のスキーマ定義"""
    attendance_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "attendance_id": self.attendance_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None
        }