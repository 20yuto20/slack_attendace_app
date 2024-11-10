from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class BreakPeriod:
    start_time: datetime
    end_time: Optional[datetime] = None

    def get_duration(self) -> float:
        """休憩時間を分単位で計算"""
        if not self.end_time:
            return 0.0
        duration = (self.end_time - self.start_time).total_seconds() / 60
        return round(duration, 2)

@dataclass
class Attendance:
    user_id: str
    user_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    break_periods: List[BreakPeriod] = None

    def __post_init__(self):
        if self.break_periods is None:
            self.break_periods = []

    def get_total_break_time(self) -> float:
        """総休憩時間を分単位で計算"""
        return sum(period.get_duration() for period in self.break_periods)

    def get_working_time(self) -> float:
        """実労働時間を分単位で計算（休憩時間を除く）"""
        if not self.end_time:
            return 0.0
        total_duration = (self.end_time - self.start_time).total_seconds() / 60
        return round(total_duration - self.get_total_break_time(), 2)

    def to_dict(self) -> dict:
        """Firestoreに保存するためのdict形式に変換"""
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "break_periods": [
                {
                    "start_time": period.start_time.isoformat(),
                    "end_time": period.end_time.isoformat() if period.end_time else None
                }
                for period in self.break_periods
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Attendance':
        """dict形式からAttendanceオブジェクトを生成"""
        break_periods = [
            BreakPeriod(
                start_time=datetime.fromisoformat(period["start_time"]),
                end_time=datetime.fromisoformat(period["end_time"]) if period.get("end_time") else None
            )
            for period in data.get("break_periods", [])
        ]
        return cls(
            user_id=data["user_id"],
            user_name=data["user_name"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            break_periods=break_periods
        )