import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from google.cloud.firestore_v1.base_query import FieldFilter

from src.models.attendance import Attendance  # 絶対パスに修正
from src.utils.time_utils import get_current_time

class FirestoreRepository:
    def __init__(self, project_id: str, credentials_path: str):
        try:
            cred = credentials.Certificate(credentials_path)
            # アプリが初期化されていない場合のみ初期化
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred, {
                    'projectId': project_id,
                })
            self.db = firestore.client()
            self.attendance_collection = self.db.collection('attendance')
            self.installations_collection = self.db.collection('slack_installations')
        except Exception as e:
            print(f"Firebase initialization error: {str(e)}")
            raise

    def create_attendance(self, attendance: Attendance) -> None:
        """
        新しい勤怠記録を作成
        - ドキュメントIDを自動生成し、attendance.doc_id に保持
        """
        doc_ref = self.attendance_collection.document()
        attendance.doc_id = doc_ref.id  # ★ 生成したIDをAttendanceにセット
        doc_ref.set(attendance.to_dict())

    def get_active_attendance(self, user_id: str, team_id: str = None) -> Optional[Attendance]:
        """
        ユーザーのアクティブな（終了していない）勤怠記録を取得
        
        Args:
            user_id: ユーザーID
            team_id: チームID (Slackワークスペース)
        """
        query = (
            self.attendance_collection
            .where(filter=FieldFilter("user_id", "==", user_id))
            .where(filter=FieldFilter("end_time", "==", None))
        )
        
        # team_idが指定されている場合はさらにフィルタリング
        if team_id:
            query = query.where(filter=FieldFilter("team_id", "==", team_id))
            
        query = query.limit(1)
        docs = query.get()
        
        for doc in docs:
            attendance = Attendance.from_dict(doc.to_dict())
            attendance.doc_id = doc.id  # ★ ドキュメントIDを保持
            return attendance
        return None
    
    def get_all_active_attendances(self, team_id: str = None) -> List[Attendance]:
        """
        すべてのアクティブな（終了していない）勤怠記録を取得
        
        Args:
            team_id: チームID (Slackワークスペース)
        
        Returns:
            List[Attendance]: アクティブな勤怠記録のリスト
        """
        query = (
            self.attendance_collection
            .where(filter=FieldFilter("end_time", "==", None))
        )
        
        # team_idが指定されている場合はワークスペースでフィルタリング
        if team_id:
            query = query.where(filter=FieldFilter("team_id", "==", team_id))
            
        query = query.limit(100)  # 上限を設定（必要に応じて調整）
        docs = query.get()
        
        active_attendances = []
        for doc in docs:
            attendance = Attendance.from_dict(doc.to_dict())
            attendance.doc_id = doc.id
            active_attendances.append(attendance)
        
        return active_attendances

    def update_attendance(self, attendance: Attendance) -> None:
        """
        ドキュメントIDを用いて勤怠記録を更新
        - すでに end_time がセットされているレコードでも問題なく上書き可能
        """
        if not attendance.doc_id:
            raise ValueError("Cannot update attendance without doc_id.")
        # doc_id で指定
        doc_ref = self.attendance_collection.document(attendance.doc_id)
        doc_ref.set(attendance.to_dict())

    def get_attendance_by_period(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime,
        team_id: str = None,
        batch_size: int = 100
    ) -> List[Attendance]:
        """
        指定期間の勤怠記録を取得
        """
        try:
            query = (
                self.attendance_collection
                .where(filter=FieldFilter("user_id", "==", user_id))
                .where(filter=FieldFilter("start_time", ">=", start_date.isoformat()))
                .where(filter=FieldFilter("start_time", "<=", end_date.isoformat()))
            )
            
            # team_idが指定されている場合はワークスペースでフィルタリング
            if team_id:
                query = query.where(filter=FieldFilter("team_id", "==", team_id))
                
            query = query.order_by("start_time").limit(batch_size)
            
            records = []
            docs = query.get()
            
            while docs:
                for d in docs:
                    attendance = self._convert_to_attendance(d)
                    records.append(attendance)
                
                # 次のバッチがあるか確認
                last_doc = docs[-1]
                docs = (
                    query
                    .start_after(last_doc)
                    .get()
                )
            
            return records
        except Exception as e:
            print(f"Error retrieving attendance records: {str(e)}")
            raise

    def _convert_to_attendance(self, doc: firestore.DocumentSnapshot) -> Attendance:
        """
        Firestoreのドキュメントを勤怠オブジェクトに変換
        - doc.id を attendance.doc_id に保持
        """
        data = doc.to_dict()
        attendance = Attendance.from_dict(data)
        attendance.doc_id = doc.id  # ★ 取得したドキュメントIDを保持
        return attendance

    def get_attendance_stats(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime,
        team_id: str = None
    ) -> Dict[str, Any]:
        """
        指定期間の勤怠統計を取得
        """
        records = self.get_attendance_by_period(user_id, start_date, end_date, team_id)
        
        total_working_time = 0
        total_break_time = 0
        daily_stats = {}
        
        for record in records:
            date_key = record.start_time.date().isoformat()
            
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    'working_time': 0,
                    'break_time': 0,
                    'attendance_count': 0
                }
            
            daily_stats[date_key]['working_time'] += record.get_working_time()
            daily_stats[date_key]['break_time'] += record.get_total_break_time()
            daily_stats[date_key]['attendance_count'] += 1
            
            total_working_time += record.get_working_time()
            total_break_time += record.get_total_break_time()
        
        return {
            'total_working_time': total_working_time,
            'total_break_time': total_break_time,
            'daily_stats': daily_stats,
            'record_count': len(records)
        }
    
    def get_all_workspaces(self) -> List[Dict[str, Any]]:
        """
        システムに登録されている全てのワークスペース情報を取得する
        
        Returns:
            List[Dict[str, Any]]: ワークスペース情報のリスト
        """
        try:
            # slack_installationsから全チームIDを取得する方法1:
            # ユーザーIDがNullのインストールレコードのみを対象にする
            installations = self.installations_collection.where(
                filter=FieldFilter("user_id", "==", None)
            ).get()
            
            # 重複排除のためのセット
            team_ids = set()
            workspaces = []
            
            for doc in installations:
                data = doc.to_dict()
                team_id = data.get("team_id")
                if team_id and team_id not in team_ids:
                    team_ids.add(team_id)
                    workspaces.append({
                        "team_id": team_id,
                        "enterprise_id": data.get("enterprise_id"),
                        "is_enterprise_install": data.get("is_enterprise_install", False)
                    })
            
            # 方法2: バックアップとして、勤怠レコードからもチームIDを収集
            # 特に勤怠レコードがあるが、installation情報が完全でない場合に有効
            if not workspaces:
                # 全勤怠記録からユニークなteam_id値を取得
                # これは非効率なため、installationsが取得できない場合の
                # フォールバックとしてのみ使用
                attendances = self.attendance_collection.limit(1000).get()
                for doc in attendances:
                    data = doc.to_dict()
                    team_id = data.get("team_id")
                    if team_id and team_id not in team_ids:
                        team_ids.add(team_id)
                        workspaces.append({"team_id": team_id})
            
            return workspaces
        except Exception as e:
            print(f"Error retrieving workspaces: {str(e)}")
            # エラー時は空リストを返す
            return []
    
    def get_attendance_by_id(self, doc_id: str) -> Optional[Attendance]:
        """
        ドキュメントIDで勤怠記録を取得
        
        Args:
            doc_id: ドキュメントID
            
        Returns:
            Optional[Attendance]: 勤怠記録オブジェクト、見つからない場合はNone
        """
        try:
            doc = self.attendance_collection.document(doc_id).get()
            if not doc.exists:
                return None
            
            attendance = self._convert_to_attendance(doc)
            return attendance
        except Exception as e:
            print(f"Error retrieving attendance by ID: {str(e)}")
            return None