from datetime import datetime, timedelta
import calendar
import csv
from io import StringIO
from typing import List, Dict, Any, Tuple

from ..models.attendance import Attendance
from ..repositories.firestore_repository import FirestoreRepository
from ..utils.time_utils import get_current_time, get_start_of_month, get_end_of_month

class MonthlySummaryService:
    def __init__(self, repository: FirestoreRepository):
        self.repository = repository

    def get_monthly_summary(self, user_id: str, year: int, month: int) -> Dict[str, Any]:
        """指定された月の勤怠サマリーを取得"""
        # 月の開始日と終了日を取得
        start_date = get_start_of_month(year, month)
        end_date = get_end_of_month(year, month)
        
        # 指定月の全ての勤怠記録を取得
        records = self.repository.get_attendance_by_period(user_id, start_date, end_date)
        
        # 日ごとの勤怠記録を集計
        daily_records = {}
        weekly_totals = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}  # 週ごとの合計時間
        total_working_time = 0
        
        for record in records:
            date = record.start_time.date()
            week_number = (date.day - 1) // 7 + 1
            
            if date not in daily_records:
                daily_records[date] = {
                    'working_time': 0,
                    'break_time': 0,
                    'week_number': week_number
                }
            
            working_time = record.get_working_time()
            break_time = record.get_total_break_time()
            
            daily_records[date]['working_time'] += working_time
            daily_records[date]['break_time'] += break_time
            weekly_totals[week_number] += working_time
            total_working_time += working_time

        return {
            'daily_records': daily_records,
            'weekly_totals': weekly_totals,
            'total_working_time': total_working_time,
            'year': year,
            'month': month
        }

    def generate_csv(self, user_id: str, user_name: str, year: int, month: int) -> Tuple[str, str]:
        """月次サマリーのCSVを生成"""
        summary = self.get_monthly_summary(user_id, year, month)
        
        # CSVファイル名を生成
        filename = f"attendance_summary_{user_name}_{year}_{month:02d}.csv"
        
        # CSVデータを生成
        output = StringIO()
        writer = csv.writer(output)
        
        # ヘッダー行を書き込み
        writer.writerow(['従業員名', user_name])
        writer.writerow(['年月', f'{year}年{month}月'])
        writer.writerow([])
        writer.writerow(['日付', '曜日', '勤務時間', '休憩時間', '週番号'])
        
        # 日々のデータを書き込み
        daily_records = summary['daily_records']
        for date in sorted(daily_records.keys()):
            record = daily_records[date]
            writer.writerow([
                date.strftime('%Y-%m-%d'),
                date.strftime('%A'),
                f"{record['working_time']:.2f}",
                f"{record['break_time']:.2f}",
                record['week_number']
            ])
        
        # 週次サマリーを書き込み
        writer.writerow([])
        writer.writerow(['週次サマリー'])
        for week, total in summary['weekly_totals'].items():
            writer.writerow([f'第{week}週', f'{total:.2f}'])
        
        # 月次合計を書き込み
        writer.writerow([])
        writer.writerow(['月間合計勤務時間', f"{summary['total_working_time']:.2f}"])
        
        return filename, output.getvalue()