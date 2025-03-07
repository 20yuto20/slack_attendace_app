from datetime import datetime
from typing import List, Dict, Any, Optional

from ..models.attendance import Attendance
from ..repositories.firestore_repository import FirestoreRepository
from ..utils.time_utils import get_current_time
from ..config import get_config

class WarningService:
    """Service for managing work/break time warnings"""
    
    def __init__(self, repository: FirestoreRepository):
        self.repository = repository
        self.config = get_config()
        # Get warning thresholds from config
        self.long_work_warning_minutes = getattr(self.config.attendance_alerts, 'long_work_warning_minutes', 480)  # 8 hours default
        self.long_break_warning_minutes = getattr(self.config.attendance_alerts, 'long_break_warning_minutes', 60)  # 1 hour default
        
    def check_long_working_users(self, team_id: str = None) -> List[Dict[str, Any]]:
        """
        Check for users who have been working too long
        
        Args:
            team_id: Optional team ID to filter by workspace
            
        Returns:
            List[Dict[str, Any]]: List of users working too long
        """
        # Get active attendances
        active_records = self.repository.get_all_active_attendances(team_id=team_id)
        
        # Get current time
        current_time = get_current_time()
        
        # Users to warn
        warning_users = []
        
        for record in active_records:
            # Skip users who are on break
            is_on_break = False
            if record.break_periods and not record.break_periods[-1].end_time:
                is_on_break = True
                
            if not is_on_break:
                # Calculate work duration
                work_duration = (current_time - record.start_time).total_seconds() / 60
                # Subtract break time
                actual_work_duration = work_duration - record.get_total_break_time()
                
                # Check if duration exceeds threshold
                if actual_work_duration >= self.long_work_warning_minutes:
                    warning_users.append({
                        'user_id': record.user_id,
                        'user_name': record.user_name,
                        'team_id': record.team_id,
                        'duration': actual_work_duration,
                        'warning_type': 'long_work',
                        'doc_id': record.doc_id
                    })
        
        return warning_users
    
    def check_long_break_users(self, team_id: str = None) -> List[Dict[str, Any]]:
        """
        Check for users who have been on break too long
        
        Args:
            team_id: Optional team ID to filter by workspace
            
        Returns:
            List[Dict[str, Any]]: List of users on break too long
        """
        # Get active attendances
        active_records = self.repository.get_all_active_attendances(team_id=team_id)
        
        # Get current time
        current_time = get_current_time()
        
        # Users to warn
        warning_users = []
        
        for record in active_records:
            # Only check users who are on break
            if record.break_periods and not record.break_periods[-1].end_time:
                # Calculate break duration
                break_start_time = record.break_periods[-1].start_time
                break_duration = (current_time - break_start_time).total_seconds() / 60
                
                # Check if duration exceeds threshold
                if break_duration >= self.long_break_warning_minutes:
                    warning_users.append({
                        'user_id': record.user_id,
                        'user_name': record.user_name,
                        'team_id': record.team_id,
                        'duration': break_duration,
                        'warning_type': 'long_break',
                        'doc_id': record.doc_id
                    })
        
        return warning_users
    
    def get_all_warnings(self, team_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all users who need warnings
        
        Args:
            team_id: Optional team ID to filter by workspace
            
        Returns:
            List[Dict[str, Any]]: List of all users needing warnings
        """
        # Get both types of warnings
        long_work_users = self.check_long_working_users(team_id=team_id)
        long_break_users = self.check_long_break_users(team_id=team_id)
        
        # Combine the lists
        return long_work_users + long_break_users
    
    def format_warning_message(self, warning_info: Dict[str, Any]) -> str:
        """
        Format a warning message as plain text
        
        Args:
            warning_info: Warning information
            
        Returns:
            str: Formatted warning message
        """
        # Format duration
        hours = int(warning_info['duration'] // 60)
        minutes = int(warning_info['duration'] % 60)
        time_str = f"{hours}時間{minutes}分" if hours > 0 else f"{minutes}分"
        
        # Create appropriate message by warning type
        if warning_info['warning_type'] == 'long_work':
            return (
                f"<@{warning_info['user_id']}> さん、勤務時間が {time_str} を超えました。\n"
                "長時間の勤務は健康に影響することがあります。\n"
                "必要に応じて休憩を取るか、退勤処理を行うことをお勧めします。 `/punch_out` コマンドで退勤できます。"
            )
        elif warning_info['warning_type'] == 'long_break':
            return (
                f"<@{warning_info['user_id']}> さん、休憩時間が {time_str} を超えました。\n"
                "休憩終了の処理を忘れていませんか？ `/break_end` コマンドで休憩終了の処理ができます。"
            )
        
        # Fallback
        return "警告が発生しています。管理者に確認してください。"
    
    def is_alert_enabled(self) -> bool:
        """
        Check if alerts are enabled in configuration
        
        Returns:
            bool: True if alerts are enabled
        """
        return getattr(self.config.attendance_alerts, 'enabled', False)