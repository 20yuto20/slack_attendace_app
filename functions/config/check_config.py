#!/usr/bin/env python

import os
import sys
from pathlib import Path
from typing import List
from dataclasses import dataclass
from colorama import init, Fore, Style
from dotenv import load_dotenv

# カラー出力の初期化
init()

@dataclass
class ConfigCheckResult:
    name: str
    value: str
    exists: bool
    is_file_exists: bool = None
    
    def get_status_color(self) -> str:
        if self.exists:
            if self.is_file_exists is None or self.is_file_exists:
                return Fore.GREEN
            return Fore.RED
        return Fore.RED

    def get_status_symbol(self) -> str:
        if self.exists:
            if self.is_file_exists is None or self.is_file_exists:
                return "✓"
            return "×"
        return "×"

def check_env_vars() -> List[ConfigCheckResult]:
    """環境変数をチェックして結果を返す"""
    required_vars = {
        "SLACK_BOT_TOKEN": "Slackボットトークン",
        "SLACK_SIGNING_SECRET": "Slack署名シークレット",
        "SLACK_CLIENT_ID": "SlackクライアントID",
        "SLACK_CLIENT_SECRET": "Slackクライアントシークレット",
        "APP_FIREBASE_PROJECT_ID": "Firebaseプロジェクトのプロジェクトid",
        "APP_FIREBASE_CREDENTIALS_PATH": "Firebase認証情報ファイルのパス"
    }
    
    results = []
    
    for var, description in required_vars.items():
        value = os.getenv(var, '')
        exists = bool(value)
        
        # Firebase認証情報ファイルの場合は、ファイルの存在もチェック
        is_file_exists = None
        if var == "APP_FIREBASE_CREDENTIALS_PATH" and exists:
            is_file_exists = Path(value).exists()
        
        results.append(ConfigCheckResult(
            name=var,
            value=value[:20] + '...' if value and len(value) > 20 else value,
            exists=exists,
            is_file_exists=is_file_exists
        ))
    
    return results

def main():
    """メイン処理"""
    try:
        # .envファイルを読み込む
        load_dotenv()
        
        print("\n=== 環境変数チェック ===\n")
        
        results = check_env_vars()
        
        # 結果の表示
        for result in results:
            status_color = result.get_status_color()
            status_symbol = result.get_status_symbol()
            
            print(f"{status_color}{status_symbol}{Style.RESET_ALL} {result.name}: ", end='')
            
            if result.exists:
                print(f"{Fore.CYAN}{result.value}{Style.RESET_ALL}")
                if result.is_file_exists is not None and not result.is_file_exists:
                    print(f"  {Fore.RED}Warning: ファイルが存在しません{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}未設定{Style.RESET_ALL}")
        
        # 成功・失敗の判定
        all_success = all(r.exists and (r.is_file_exists is None or r.is_file_exists) for r in results)
        
        print("\n=== チェック結果 ===")
        if all_success:
            print(f"{Fore.GREEN}✓ すべての設定が正常です{Style.RESET_ALL}")
            sys.exit(0)
        else:
            print(f"{Fore.RED}× 一部の設定に問題があります{Style.RESET_ALL}")
            sys.exit(1)
            
    except Exception as e:
        print(f"{Fore.RED}エラーが発生しました: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()