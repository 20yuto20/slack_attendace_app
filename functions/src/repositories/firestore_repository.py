import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import Optional, List, Dict, Any
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

    def get_active_attendance(self, user_id: str) -> Optional[Attendance]:
        """
        ユーザーのアクティブな（終了していない）勤怠記録を取得
        """
        query = (
            self.attendance_collection
            .where(filter=firestore.FieldFilter("user_id", "==", user_id))
            .where(filter=firestore.FieldFilter("end_time", "==", None))
            .limit(1)
        )
        docs = query.get()
        
        for doc in docs:
            attendance = Attendance.from_dict(doc.to_dict())
            attendance.doc_id = doc.id  # ★ ドキュメントIDを保持
            return attendance
        return None

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
                .order_by("start_time")
                .limit(batch_size)
            )
            
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
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        指定期間の勤怠統計を取得
        """
        records = self.get_attendance_by_period(user_id, start_date, end_date)
        
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
