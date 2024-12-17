from typing import Optional, Dict, Any
import json
from datetime import datetime
from firebase_admin import firestore
from slack_sdk.oauth.installation_store import InstallationStore
from slack_sdk.oauth.installation_store.models.installation import Installation
from slack_sdk.oauth.installation_store.models.bot import Bot

class FirestoreInstallationStore(InstallationStore):
    """Firestoreベースのインストール情報永続化クラス"""
    
    def __init__(self, db: firestore.Client):
        self.db = db
        self.installations_collection = self.db.collection('slack_installations')
        self.bots_collection = self.db.collection('slack_bots')

    def save(self, installation: Installation):
        """インストール情報を保存"""
        # 基本のインストール情報（ユーザーIDありの場合）
        installation_data = {
            'app_id': installation.app_id,
            'enterprise_id': installation.enterprise_id,
            'team_id': installation.team_id,
            'user_id': installation.user_id,
            'bot_token': installation.bot_token,
            'bot_id': installation.bot_id,
            'bot_user_id': installation.bot_user_id,
            'bot_scopes': installation.bot_scopes,
            'user_token': installation.user_token,
            'user_scopes': installation.user_scopes,
            'installed_at': datetime.utcnow(),
            'is_enterprise_install': installation.is_enterprise_install,
        }

        # ユーザーIDありドキュメントID
        user_doc_id = self._generate_installation_id(
            enterprise_id=installation.enterprise_id,
            team_id=installation.team_id,
            is_enterprise_install=installation.is_enterprise_install,
            user_id=installation.user_id
        )
        self.installations_collection.document(user_doc_id).set(installation_data)

        # ボットトークンがある場合、user_idなしのワークスペース/エンタープライズ単位のドキュメントも保存する
        # これにより、user_idを指定しなくてもbotインストール情報が取得可能になる
        if installation.bot_token:
            bot_level_doc_id = self._generate_installation_id(
                enterprise_id=installation.enterprise_id,
                team_id=installation.team_id,
                is_enterprise_install=installation.is_enterprise_install,
                user_id=None  # userなし
            )
            bot_level_data = dict(installation_data)
            bot_level_data['user_id'] = None
            self.installations_collection.document(bot_level_doc_id).set(bot_level_data)

            # Bot情報も保存
            bot_data = {
                'app_id': installation.app_id,
                'enterprise_id': installation.enterprise_id,
                'team_id': installation.team_id,
                'bot_token': installation.bot_token,
                'bot_id': installation.bot_id,
                'bot_user_id': installation.bot_user_id,
                'bot_scopes': installation.bot_scopes,
                'installed_at': datetime.utcnow(),
                'is_enterprise_install': installation.is_enterprise_install,
            }
            
            bot_doc_id = self._generate_bot_id(
                enterprise_id=installation.enterprise_id,
                team_id=installation.team_id,
                is_enterprise_install=installation.is_enterprise_install
            )
            self.bots_collection.document(bot_doc_id).set(bot_data)

    def find_installation(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        user_id: Optional[str] = None,
        is_enterprise_install: Optional[bool] = False,
    ) -> Optional[Installation]:
        """インストール情報を検索"""
        doc_id = self._generate_installation_id(
            enterprise_id=enterprise_id,
            team_id=team_id,
            is_enterprise_install=is_enterprise_install,
            user_id=user_id
        )
        
        doc = self.installations_collection.document(doc_id).get()
        if not doc.exists:
            # user_idなしで検索できなかった場合、user_idがNoneでないなら再度Noneで検索
            # ただしSlack Boltはデフォルトでuser_id無し検索を行うことが多いので、
            # user_idが指定されていない場合はこれ以上再検索は不要。
            if user_id is not None:
                # user_idがある検索で見つからなかった場合、user_idなしで再検索してみる
                no_user_doc_id = self._generate_installation_id(
                    enterprise_id=enterprise_id,
                    team_id=team_id,
                    is_enterprise_install=is_enterprise_install,
                    user_id=None
                )
                doc = self.installations_collection.document(no_user_doc_id).get()
                if not doc.exists:
                    return None
                return self._create_installation_from_doc(doc)
            return None
            
        return self._create_installation_from_doc(doc)

    def find_bot(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        is_enterprise_install: Optional[bool] = False
    ) -> Optional[Bot]:
        """Bot情報を検索"""
        doc_id = self._generate_bot_id(
            enterprise_id=enterprise_id,
            team_id=team_id,
            is_enterprise_install=is_enterprise_install
        )
        
        doc = self.bots_collection.document(doc_id).get()
        if not doc.exists:
            return None
            
        return self._create_bot_from_doc(doc)

    def delete_installation(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        user_id: Optional[str] = None,
        is_enterprise_install: Optional[bool] = False
    ) -> None:
        """インストール情報を削除"""
        doc_id = self._generate_installation_id(
            enterprise_id=enterprise_id,
            team_id=team_id,
            is_enterprise_install=is_enterprise_install,
            user_id=user_id
        )
        
        self.installations_collection.document(doc_id).delete()

        # ボットレベルのドキュメントも削除
        if user_id is not None:
            bot_level_doc_id = self._generate_installation_id(
                enterprise_id=enterprise_id,
                team_id=team_id,
                is_enterprise_install=is_enterprise_install,
                user_id=None
            )
            self.installations_collection.document(bot_level_doc_id).delete()

    def delete_bot(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        is_enterprise_install: Optional[bool] = False
    ) -> None:
        """Bot情報を削除"""
        doc_id = self._generate_bot_id(
            enterprise_id=enterprise_id,
            team_id=team_id,
            is_enterprise_install=is_enterprise_install
        )
        
        self.bots_collection.document(doc_id).delete()

    def _generate_installation_id(
        self,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        is_enterprise_install: bool,
        user_id: Optional[str]
    ) -> str:
        """インストール情報のドキュメントID生成"""
        components = []
        if is_enterprise_install and enterprise_id:
            # エンタープライズインストールの場合
            components.append(f"E{enterprise_id}")
            if user_id:
                components.append(f"U{user_id}")
        else:
            # 通常のワークスペースインストール
            if enterprise_id:
                components.append(f"E{enterprise_id}")
            if team_id:
                components.append(f"T{team_id}")
            if user_id:
                components.append(f"U{user_id}")
        return "-".join(components)

    def _generate_bot_id(
        self,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        is_enterprise_install: bool
    ) -> str:
        """BotのドキュメントID生成"""
        components = []
        if is_enterprise_install and enterprise_id:
            components.append(f"E{enterprise_id}")
        else:
            if enterprise_id:
                components.append(f"E{enterprise_id}")
            if team_id:
                components.append(f"T{team_id}")
        return "-".join(components)

    def _create_installation_from_doc(self, doc) -> Installation:
        """FirestoreドキュメントからInstallationオブジェクトを作成"""
        data = doc.to_dict()
        return Installation(
            app_id=data.get('app_id'),
            enterprise_id=data.get('enterprise_id'),
            team_id=data.get('team_id'),
            user_id=data.get('user_id'),
            bot_token=data.get('bot_token'),
            bot_id=data.get('bot_id'),
            bot_user_id=data.get('bot_user_id'),
            bot_scopes=data.get('bot_scopes', []),
            user_token=data.get('user_token'),
            user_scopes=data.get('user_scopes', []),
            is_enterprise_install=data.get('is_enterprise_install', False)
        )

    def _create_bot_from_doc(self, doc) -> Bot:
        """FirestoreドキュメントからBotオブジェクトを作成"""
        data = doc.to_dict()
        return Bot(
            app_id=data.get('app_id'),
            enterprise_id=data.get('enterprise_id'),
            team_id=data.get('team_id'),
            bot_token=data.get('bot_token'),
            bot_id=data.get('bot_id'),
            bot_user_id=data.get('bot_user_id'),
            bot_scopes=data.get('bot_scopes', []),
            is_enterprise_install=data.get('is_enterprise_install', False)
        )
