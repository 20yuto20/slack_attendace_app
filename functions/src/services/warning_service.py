from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional

from ..models.attendance import Attendance
from ..repositories.firestore_repository import FirestoreRepository
from ..utils.time_utils import get_current_time
from ..config import get_config
from ..slack.message_builder import MessageBuilder

class WarningService:
    """勤務時間・休憩時間の警告を管理するサービス"""
    
    def __init__(self, repository: FirestoreRepository):
        self.repository = repository
        self.config = get_config()
        # 設定ファイルから警告閾値を読み込み
        self.long_work_warning_minutes = self.config.attendance_alerts.long_work_warning_minutes
        self.long_break_warning_minutes = self.config.attendance_alerts.long_break_warning_minutes
        
    def check_long_working_users(self, team_id: str = None) -> List[Dict[str, Any]]:
        """
        長時間勤務中のユーザーをチェック
        
        Args:
            team_id: チームID (Slackワークスペース)
            
        Returns:
            List[Dict[str, Any]]: 長時間勤務中のユーザー情報リスト
        """
        # アクティブな勤怠記録を取得
        active_records = self.repository.get_all_active_attendances(team_id=team_id)
        
        # 現在時刻を取得
        current_time = get_current_time()
        
        # 警告対象のユーザーリスト
        warning_users = []
        
        for record in active_records:
            # 休憩中ではないユーザーが対象
            is_on_break = False
            if record.break_periods and not record.break_periods[-1].end_time:
                is_on_break = True
                
            if not is_on_break:
                # 勤務開始からの経過時間を計算
                work_duration = (current_time - record.start_time).total_seconds() / 60
                # 休憩時間を差し引く
                actual_work_duration = work_duration - record.get_total_break_time()
                
                # 設定された閾値を超えている場合は警告対象
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
        長時間休憩中のユーザーをチェック
        
        Args:
            team_id: チームID (Slackワークスペース)
            
        Returns:
            List[Dict[str, Any]]: 長時間休憩中のユーザー情報リスト
        """
        # アクティブな勤怠記録を取得
        active_records = self.repository.get_all_active_attendances(team_id=team_id)
        
        # 現在時刻を取得
        current_time = get_current_time()
        
        # 警告対象のユーザーリスト
        warning_users = []
        
        for record in active_records:
            # 休憩中のユーザーが対象
            if record.break_periods and not record.break_periods[-1].end_time:
                # 休憩開始からの経過時間を計算
                break_start_time = record.break_periods[-1].start_time
                break_duration = (current_time - break_start_time).total_seconds() / 60
                
                # 設定された閾値を超えている場合は警告対象
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
        すべての警告対象ユーザーを取得
        
        Args:
            team_id: チームID (Slackワークスペース)
            
        Returns:
            List[Dict[str, Any]]: 警告対象のユーザー情報リスト
        """
        # 長時間勤務のユーザーを取得
        long_work_users = self.check_long_working_users(team_id=team_id)
        
        # 長時間休憩のユーザーを取得
        long_break_users = self.check_long_break_users(team_id=team_id)
        
        # 両方のリストを結合
        return long_work_users + long_break_users
    
    def format_warning_message(self, warning_info: Dict[str, Any]) -> str:
        """
        警告メッセージを整形
        
        Args:
            warning_info: 警告情報
            
        Returns:
            str: 整形された警告メッセージ
        """
        # MessageBuilderのメソッドを使用するようにリファクタリング
        blocks = MessageBuilder.create_warning_message(
            warning_type=warning_info['warning_type'],
            user_id=warning_info['user_id'],
            user_name=warning_info['user_name'],
            duration=warning_info['duration']
        )
        
        # テキストメッセージを生成（簡易版）
        if warning_info['warning_type'] == 'long_work':
            hours = int(warning_info['duration'] // 60)
            minutes = int(warning_info['duration'] % 60)
            time_str = f"{hours}時間{minutes}分" if hours > 0 else f"{minutes}分"
            
            return (
                f"<@{warning_info['user_id']}> さん、勤務時間が {time_str} を超えました。\n"
                "長時間の勤務は健康に影響することがあります。\n"
                "必要に応じて休憩を取るか、退勤処理を行うことをお勧めします。 `/punch_out` コマンドで退勤できます。"
            )
        elif warning_info['warning_type'] == 'long_break':
            hours = int(warning_info['duration'] // 60)
            minutes = int(warning_info['duration'] % 60)
            time_str = f"{hours}時間{minutes}分" if hours > 0 else f"{minutes}分"
            
            return (
                f"<@{warning_info['user_id']}> さん、休憩時間が {time_str} を超えました。\n"
                "休憩終了の処理を忘れていませんか？ `/break_end` コマンドで休憩終了の処理ができます。"
            )
        
        return "警告が発生しています。管理者に確認してください。"
    
    def is_alert_enabled(self) -> bool:
        """
        警告機能が有効かどうかを確認
        
        Returns:
            bool: 警告機能が有効ならTrue
        """
        return getattr(self.config.attendance_alerts, 'enabled', False)