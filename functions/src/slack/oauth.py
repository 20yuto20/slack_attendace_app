# src/slack/oauth.py

import os
from slack_bolt.oauth.oauth_settings import OAuthSettings
from firebase_admin import firestore
from .store.firestore_installation_store import FirestoreInstallationStore
from .store.firestore_state_store import FirestoreStateStore

def setup_oauth_flow(client_id: str, client_secret: str, db: firestore.Client):
    """OAuthフローの設定を行う"""
    
    # インストール情報と状態管理用のストアを初期化
    installation_store = FirestoreInstallationStore(db)
    state_store = FirestoreStateStore(db)

    # スコープ設定
    # 'bot'スコープを削除し、'files:write:user'を使用
    SCOPES = [
        "chat:write",
        "commands",
        "files:write",
        "users:read",
        "users:read.email"
    ]

    base_url = os.getenv("SLACK_APP_BASE_URL", "https://slack-bot-function-2vwbe2ah2q-uc.a.run.app")
    
    oauth_settings = OAuthSettings(
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
        installation_store=installation_store,
        state_store=state_store,
        install_path="/slack/install",
        redirect_uri_path="/slack/oauth_redirect",
        redirect_uri=f"{base_url}/slack/oauth_redirect",
        success_url="/slack/oauth_success",
        failure_url="/slack/oauth_failure"
    )
    
    return oauth_settings
