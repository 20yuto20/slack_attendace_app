from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

from src.models.attendance import Attendance
from src.repositories.firestore_repository import FirestoreRepository
from src.utils.time_utils import get_current_time

class StatusService:
    """従業員の現在の勤怠状態を管理するサービス"""
    
    def __init__(self, repository: FirestoreRepository):
        self.repository = repository
    
    def get_active_employees(self, team_id: str) -> List[Dict[str, Any]]:
        """
        現在アクティブな（出勤中または休憩中の）従業員の状態一覧を取得
        
        Args:
            team_id: チームID (Slackワークスペース)
            
        Returns:
            List[Dict[str, Any]]: アクティブな従業員の状態情報リスト
        """
        # アクティブな（終了していない）勤怠記録を特定のワークスペースのみ取得
        active_records = self.repository.get_all_active_attendances(team_id=team_id)
        
        # 現在時刻を取得（経過時間計算用）
        current_time = get_current_time()
        
        # 各従業員の状態情報を構築
        employee_statuses = []
        for record in active_records:
            # 休憩中かどうかの判定
            is_on_break = False
            break_start_time = None
            
            if record.break_periods and not record.break_periods[-1].end_time:
                is_on_break = True
                break_start_time = record.break_periods[-1].start_time
            
            # 勤務開始からの経過時間（分）
            working_duration = (current_time - record.start_time).total_seconds() / 60
            
            # 休憩中の場合は休憩開始からの経過時間も計算
            break_duration = None
            if is_on_break and break_start_time:
                break_duration = (current_time - break_start_time).total_seconds() / 60
            
            # 状態情報の構築
            status_info = {
                'user_id': record.user_id,
                'user_name': record.user_name,
                'team_id': record.team_id,
                'status': 'on_break' if is_on_break else 'working',
                'start_time': record.start_time,
                'working_duration': working_duration,  # 勤務開始からの経過時間（分）
                'break_duration': break_duration,  # 休憩開始からの経過時間（分）、休憩中でない場合はNone
                'total_break_time': record.get_total_break_time()  # これまでの休憩時間合計（分）
            }
            
            employee_statuses.append(status_info)
        
        return employee_statuses
    
    def get_employee_status(self, user_id: str, team_id: str) -> Optional[Dict[str, Any]]:
        """
        特定の従業員の現在の状態を取得
        
        Args:
            user_id: Slack ユーザーID
            team_id: チームID (Slackワークスペース)
            
        Returns:
            Optional[Dict[str, Any]]: 従業員の状態情報、アクティブでない場合はNone
        """
        active_attendance = self.repository.get_active_attendance(user_id, team_id=team_id)
        
        if not active_attendance:
            return None
        
        # 現在時刻を取得（経過時間計算用）
        current_time = get_current_time()
        
        # 休憩中かどうかの判定
        is_on_break = False
        break_start_time = None
        
        if active_attendance.break_periods and not active_attendance.break_periods[-1].end_time:
            is_on_break = True
            break_start_time = active_attendance.break_periods[-1].start_time
        
        # 勤務開始からの経過時間（分）
        working_duration = (current_time - active_attendance.start_time).total_seconds() / 60
        
        # 休憩中の場合は休憩開始からの経過時間も計算
        break_duration = None
        if is_on_break and break_start_time:
            break_duration = (current_time - break_start_time).total_seconds() / 60
        
        # 状態情報の構築
        return {
            'user_id': active_attendance.user_id,
            'user_name': active_attendance.user_name,
            'team_id': active_attendance.team_id,
            'status': 'on_break' if is_on_break else 'working',
            'start_time': active_attendance.start_time,
            'working_duration': working_duration,  # 勤務開始からの経過時間（分）
            'break_duration': break_duration,  # 休憩開始からの経過時間（分）、休憩中でない場合はNone
            'total_break_time': active_attendance.get_total_break_time()  # これまでの休憩時間合計（分）
        }