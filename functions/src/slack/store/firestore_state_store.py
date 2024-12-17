from datetime import datetime, timedelta
from typing import Optional
from firebase_admin import firestore
from slack_sdk.oauth.state_store import OAuthStateStore
import secrets

class FirestoreStateStore(OAuthStateStore):
    """Firestoreベースの認証状態管理クラス"""
    
    def __init__(
        self,
        db: firestore.Client,
        expiration_seconds: int = 600
    ):
        self.db = db
        self.expiration_seconds = expiration_seconds
        self.states_collection = self.db.collection('slack_oauth_states')

    def issue(self, expire_in: Optional[int] = None) -> str:
        """
        新しいstateを発行して返す
        
        BoltのOAuthStateStoreでexpectされるインターフェース:
        issue()は引数なしで呼ばれ、state文字列を返すことが求められます。
        """
        if expire_in is None:
            expire_in = self.expiration_seconds
            
        # ランダムなstateを生成
        state = secrets.token_urlsafe(32)
        expire_at = datetime.utcnow() + timedelta(seconds=expire_in)
        
        try:
            self.states_collection.document(state).set({
                'state': state,
                'expire_at': expire_at
            })
            return state
        except Exception as e:
            print(f"Error issuing state: {str(e)}")
            # エラー時は空文字列など返してもよいが、基本的にはraiseする
            raise

    def consume(self, state: str) -> bool:
        """
        状態を検証して消費
        
        Args:
            state: 検証するstate文字列
            
        Returns:
            bool: 検証が成功したかどうか
        """
        try:
            doc_ref = self.states_collection.document(state)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
                
            data = doc.to_dict()
            expire_at = data.get('expire_at')
            
            if expire_at and expire_at.replace(tzinfo=None) < datetime.utcnow():
                doc_ref.delete()
                return False
                
            doc_ref.delete()
            return True
        except Exception as e:
            print(f"Error consuming state: {str(e)}")
            return False
