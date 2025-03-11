"""
カスタムOAuth処理モジュール - Slack BoltのOAuth処理をバイパスして直接実装
"""
import os
import logging
import requests
from firebase_admin import firestore
from flask import Request, Response, redirect
from slack_sdk.oauth.installation_store.models.installation import Installation
from urllib.parse import urlencode

# ロガー設定
logger = logging.getLogger(__name__)

class CustomOAuthHandler:
    """カスタムOAuth処理を実装するクラス"""
    
    def __init__(self, client_id, client_secret, db):
        self.client_id = client_id
        self.client_secret = client_secret
        self.db = db
        self.installations_collection = self.db.collection('slack_installations')
        self.bots_collection = self.db.collection('slack_bots')

    def handle_oauth_redirect(self, request: Request) -> Response:
        """OAuth リダイレクトを直接処理する"""
        logger.info("Handling OAuth redirect with custom handler")
        
        # コードの取得
        code = request.args.get('code')
        if not code:
            logger.error("No code parameter in OAuth redirect")
            return self._redirect_to_failure("missing_code")
        
        logger.info(f"Received OAuth code: {code[:10]}...")
        
        # Slackトークン取得APIを直接呼び出し
        try:
            # base_urlの取得
            base_url = self._get_base_url()
            redirect_uri = f"{base_url}/slack/oauth_redirect"
            
            logger.info(f"Using redirect_uri: {redirect_uri}")
            
            # Slack APIを呼び出してトークン取得
            resp = requests.post(
                "https://slack.com/api/oauth.v2.access",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri
                }
            )
            
            result = resp.json()
            
            if not result.get("ok", False):
                error = result.get("error", "unknown_error")
                logger.error(f"Slack API error: {error}")
                return self._redirect_to_failure(error)
            
            # インストール情報の保存
            self._save_installation(result)
            
            # 成功ページにリダイレクト
            return redirect("/slack/oauth_success")
            
        except Exception as e:
            logger.error(f"Error in custom OAuth handler: {str(e)}", exc_info=True)
            return self._redirect_to_failure("internal_error")
    
    def _save_installation(self, api_response):
        """Slack APIレスポンスからインストール情報を保存する"""
        try:
            # レスポンスデータの取得
            team = api_response.get("team", {})
            team_id = team.get("id")
            enterprise = api_response.get("enterprise", {})
            enterprise_id = enterprise.get("id") if enterprise else None
            
            # OAuth 2.0形式のレスポンスから必要なデータを抽出
            authed_user = api_response.get("authed_user", {})
            user_id = authed_user.get("id")
            user_token = authed_user.get("access_token")
            user_scopes = authed_user.get("scope", "").split(",") if authed_user.get("scope") else []
            
            # ボット情報
            bot_user_id = api_response.get("bot_user_id")
            bot_token = api_response.get("access_token")
            bot_scopes = api_response.get("scope", "").split(",") if api_response.get("scope") else []
            
            # App IDはトークンから推測（実際のアプリIDはAPIレスポンスから取得するのが理想的）
            app_id = bot_token.split("-")[0] if bot_token and "-" in bot_token else None
            is_enterprise_install = api_response.get("is_enterprise_install", False)
            
            # ユーザーインストール情報
            if user_id:
                user_installation_data = {
                    "app_id": app_id,
                    "enterprise_id": enterprise_id,
                    "team_id": team_id,
                    "user_id": user_id,
                    "bot_token": bot_token,
                    "bot_id": None,  # APIレスポンスからは取得できない場合がある
                    "bot_user_id": bot_user_id,
                    "bot_scopes": bot_scopes,
                    "user_token": user_token,
                    "user_scopes": user_scopes,
                    "installed_at": firestore.SERVER_TIMESTAMP,
                    "is_enterprise_install": is_enterprise_install,
                }
                
                # ドキュメントID生成
                user_doc_id = self._generate_installation_id(
                    enterprise_id=enterprise_id,
                    team_id=team_id,
                    is_enterprise_install=is_enterprise_install,
                    user_id=user_id
                )
                
                # ユーザーレベルのインストール情報を保存
                self.installations_collection.document(user_doc_id).set(user_installation_data)
                logger.info(f"Saved user installation for {user_id} in team {team_id}")
            
            # ワークスペースレベルのインストール情報
            if team_id:
                team_installation_data = {
                    "app_id": app_id,
                    "enterprise_id": enterprise_id,
                    "team_id": team_id,
                    "user_id": None,  # ワークスペースレベルではNULL
                    "bot_token": bot_token,
                    "bot_id": None,
                    "bot_user_id": bot_user_id,
                    "bot_scopes": bot_scopes,
                    "installed_at": firestore.SERVER_TIMESTAMP,
                    "is_enterprise_install": is_enterprise_install,
                }
                
                # ドキュメントID生成
                team_doc_id = self._generate_installation_id(
                    enterprise_id=enterprise_id,
                    team_id=team_id,
                    is_enterprise_install=is_enterprise_install,
                    user_id=None
                )
                
                # ワークスペースレベルのインストール情報を保存
                self.installations_collection.document(team_doc_id).set(team_installation_data)
                logger.info(f"Saved team installation for team {team_id}")
                
                # ボット情報も保存
                bot_data = {
                    "app_id": app_id,
                    "enterprise_id": enterprise_id,
                    "team_id": team_id,
                    "bot_token": bot_token,
                    "bot_id": None,
                    "bot_user_id": bot_user_id,
                    "bot_scopes": bot_scopes,
                    "installed_at": firestore.SERVER_TIMESTAMP,
                    "is_enterprise_install": is_enterprise_install,
                }
                
                bot_doc_id = self._generate_bot_id(
                    enterprise_id=enterprise_id,
                    team_id=team_id,
                    is_enterprise_install=is_enterprise_install
                )
                
                self.bots_collection.document(bot_doc_id).set(bot_data)
                logger.info(f"Saved bot information for team {team_id}")
                
            return True
        except Exception as e:
            logger.error(f"Error saving installation: {str(e)}", exc_info=True)
            raise

    def _generate_installation_id(self, enterprise_id, team_id, is_enterprise_install, user_id):
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

    def _generate_bot_id(self, enterprise_id, team_id, is_enterprise_install):
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
    
    def _redirect_to_failure(self, error):
        """失敗ページにリダイレクト"""
        url = f"/slack/oauth_failure?error={error}"
        return redirect(url)
    
    def _get_base_url(self):
        """ベースURLの取得"""
        # 優先順位: 1. SLACK_APP_BASE_URL、2. FUNCTION_URL、3. 構築URL
        base_url = os.getenv("SLACK_APP_BASE_URL")
        if not base_url:
            request_url = os.getenv("FUNCTION_URL")
            if request_url:
                base_url = request_url
            else:
                project_id = os.getenv("GCP_PROJECT", "slack-attendance-bot-4a3a5")
                region = os.getenv("FUNCTION_REGION", "us-central1")
                base_url = f"https://{region}-{project_id}.cloudfunctions.net"
        
        return base_url