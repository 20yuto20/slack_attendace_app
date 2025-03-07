#!/usr/bin/env python
"""
既存の勤怠データにteam_idフィールドを追加するマイグレーションスクリプト（修正版）
存在しないフィールドと値がNullのフィールドを区別するように修正

使用方法:
python migrate_add_team_id_fixed.py --project-id=slack-attendance-bot-4a3a5 --credentials-path=/path/to/firebase-credentials.json --team-id=TXXX123456
"""

import argparse
import firebase_admin
from firebase_admin import credentials, firestore
from tqdm import tqdm

def parse_arguments():
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(description='既存の勤怠データにteam_idを追加')
    
    parser.add_argument('--project-id', required=True, help='Firebaseプロジェクトのプロジェクトid')
    parser.add_argument('--credentials-path', required=True, help='Firebase認証情報ファイルのパス')
    parser.add_argument('--team-id', required=True, help='追加するSlackワークスペースID')
    parser.add_argument('--batch-size', type=int, default=100, help='一度に処理するドキュメントの数（デフォルト: 100）')
    parser.add_argument('--dry-run', action='store_true', help='実際の更新は行わず、対象ドキュメントの数を表示するのみ')
    
    return parser.parse_args()

def main():
    """メイン処理"""
    args = parse_arguments()
    
    # Firebaseを初期化
    try:
        cred = credentials.Certificate(args.credentials_path)
        firebase_admin.initialize_app(cred, {
            'projectId': args.project_id,
        })
        db = firestore.client()
    except Exception as e:
        print(f"Firebase初期化エラー: {e}")
        return
    
    # 勤怠記録コレクションを取得
    attendance_collection = db.collection('attendance')
    
    # すべてのドキュメントを取得
    all_docs = attendance_collection.limit(10000).get()
    
    # team_idフィールドがないドキュメントをフィルタリング
    docs_to_update = []
    for doc in all_docs:
        data = doc.to_dict()
        if 'team_id' not in data:
            docs_to_update.append(doc)
    
    if not docs_to_update:
        print("team_idフィールドがないドキュメントはありませんでした。")
        return
    
    print(f"team_idフィールドがない勤怠記録: {len(docs_to_update)}件")
    
    if args.dry_run:
        print("ドライランモード: 実際の更新は行いません。")
        for doc in docs_to_update[:5]:
            print(f"- ドキュメントID: {doc.id}")
        return
    
    # 確認
    answer = input(f"これらの記録に team_id: '{args.team_id}' を追加しますか？ (yes/no): ")
    if answer.lower() != 'yes':
        print("操作をキャンセルしました。")
        return
    
    # バッチ更新を準備
    batch_size = args.batch_size
    batch_count = 0
    total_updated = 0
    
    for i in tqdm(range(0, len(docs_to_update), batch_size)):
        batch = db.batch()
        chunk = docs_to_update[i:i+batch_size]
        
        for doc in chunk:
            # 現在のデータを取得
            doc_data = doc.to_dict()
            
            # team_idを追加
            doc_data['team_id'] = args.team_id
            
            # バッチ更新に追加
            doc_ref = attendance_collection.document(doc.id)
            batch.update(doc_ref, doc_data)
        
        # バッチ更新を実行
        batch.commit()
        batch_count += 1
        total_updated += len(chunk)
        
        print(f"バッチ {batch_count} 完了: {len(chunk)}件更新")
    
    print(f"マイグレーション完了: 合計 {total_updated}件の記録を更新しました。")

if __name__ == "__main__":
    main()