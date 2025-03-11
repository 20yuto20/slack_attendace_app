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
    BOT_SCOPES = [
        "chat:write",
        "commands",
        "files:write",
        "users:read",
        "users:read.email",
        "app_mentions:read",
        "channels:read"
    ]

    USER_SCOPES = [
        "users.profile:write"
    ]
    
    # より堅牢なベースURL取得方法
    request_url = os.getenv("FUNCTION_URL")
    project_id = os.getenv("GCP_PROJECT", "slack-attendance-bot-4a3a5")
    region = os.getenv("FUNCTION_REGION", "us-central1")
    
    # 優先順位: 1. SLACK_APP_BASE_URL、2. FUNCTION_URL、3. 構築URL
    base_url = os.getenv("SLACK_APP_BASE_URL")
    if not base_url:
        if request_url:
            base_url = request_url
        else:
            base_url = f"https://{region}-{project_id}.cloudfunctions.net"
    
    print(f"Using base_url: {base_url} for Slack OAuth")
    
    oauth_settings = OAuthSettings(
        client_id=client_id,
        client_secret=client_secret,
        scopes=BOT_SCOPES,
        user_scopes=USER_SCOPES,
        installation_store=installation_store,
        state_store=state_store,
        install_path="/slack/install",
        redirect_uri_path="/slack/oauth_redirect",
        redirect_uri=f"{base_url}/slack/oauth_redirect",
        success_url="/slack/oauth_success",
        failure_url="/slack/oauth_failure"
    )
    
    return oauth_settings