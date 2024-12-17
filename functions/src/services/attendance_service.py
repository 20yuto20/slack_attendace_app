from datetime import datetime
from typing import Optional, Tuple

from src.models.attendance import Attendance, BreakPeriod
from src.repositories.firestore_repository import FirestoreRepository
from src.utils.time_utils import get_current_time

class AttendanceService:
    def __init__(self, repository: FirestoreRepository):
        self.repository = repository

    def punch_in(self, user_id: str, user_name: str) -> Tuple[bool, str, Optional[datetime]]:
        """出勤処理"""
        active_attendance = self.repository.get_active_attendance(user_id)
        if active_attendance:
            return False, "既に出勤済みです。", None

        current_time = get_current_time()
        attendance = Attendance(
            user_id=user_id,
            user_name=user_name,
            start_time=current_time
        )
        self.repository.create_attendance(attendance)
        return True, "出勤を記録しました。", current_time

    def punch_out(self, user_id: str) -> Tuple[bool, str, Optional[Attendance]]:
        """退勤処理"""
        active_attendance = self.repository.get_active_attendance(user_id)
        if not active_attendance:
            return False, "出勤記録が見つかりません。", None

        if active_attendance.break_periods and not active_attendance.break_periods[-1].end_time:
            return False, "休憩中は退勤できません。まず休憩を終了してください。", None

        active_attendance.end_time = get_current_time()
        self.repository.update_attendance(active_attendance)
        return True, "退勤を記録しました。", active_attendance

    def start_break(self, user_id: str) -> Tuple[bool, str, Optional[datetime]]:
        """休憩開始処理"""
        active_attendance = self.repository.get_active_attendance(user_id)
        if not active_attendance:
            return False, "出勤記録が見つかりません。", None

        if active_attendance.break_periods and not active_attendance.break_periods[-1].end_time:
            return False, "既に休憩中です。", None

        current_time = get_current_time()
        active_attendance.break_periods.append(BreakPeriod(start_time=current_time))
        self.repository.update_attendance(active_attendance)
        return True, "休憩を開始しました。", current_time

    def end_break(self, user_id: str) -> Tuple[bool, str, Optional[Tuple[datetime, float]]]:
        """休憩終了処理"""
        active_attendance = self.repository.get_active_attendance(user_id)
        if not active_attendance:
            return False, "出勤記録が見つかりません。", None

        if not active_attendance.break_periods or active_attendance.break_periods[-1].end_time:
            return False, "休憩が開始されていません。", None

        current_time = get_current_time()
        active_attendance.break_periods[-1].end_time = current_time
        break_duration = active_attendance.break_periods[-1].get_duration()
        
        self.repository.update_attendance(active_attendance)
        return True, "休憩を終了しました。", (current_time, break_duration)