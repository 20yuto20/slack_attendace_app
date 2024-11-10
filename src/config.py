import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

from omegaconf import OmegaConf

_config = None

def init_config() -> Any:
    """設定を初期化"""
    global _config
    
    if _config is not None:
        return _config

    # .envファイルを読み込む
    load_dotenv()
    
    # デフォルトの設定ファイルのパス
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    
    # 基本設定の読み込み
    _config = OmegaConf.load(config_path)
    
    # 環境変数で上書き
    env_config = OmegaConf.create({
        "slack": {
            "bot_token": os.getenv("SLACK_BOT_TOKEN"),
            "signing_secret": os.getenv("SLACK_SIGNING_SECRET"),
            "app_token": os.getenv("SLACK_APP_TOKEN"),
        },
        "firebase": {
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "credentials_path": os.getenv("FIREBASE_CREDENTIALS_PATH"),
        }
    })
    
    _config = OmegaConf.merge(_config, env_config)
    return _config

def get_config() -> Any:
    """設定を取得"""
    global _config
    if _config is None:
        _config = init_config()
    return _config