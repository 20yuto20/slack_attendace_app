# Attendance Management Slack Bot (Version 0.0.1)

Firebase Functions と Slack Bolt for Python を使用した勤怠管理用 Slack Botです。  
このバージョン1では、Slackコマンドを用いた簡易的な勤怠記録・休憩記録・月次サマリー参照を行うことができます。

## 機能

- `/punch_in` - 出勤を記録
- `/punch_out` - 退勤を記録（実働時間と休憩時間を計算して表示）
- `/break_begin` - 休憩開始を記録
- `/break_end` - 休憩終了を記録
- `/summary` - 月次サマリーを参照（特定の年・月を選択可能）
- 月次サマリー画面からCSVダウンロードが可能

## セットアップ

### 必要条件

- Python 3.8以上
- Firebase CLIツール
- Slackワークスペースの管理者権限
- Firebaseプロジェクト（Cloud Functionsで動作）

### 環境変数の設定

以下の環境変数を設定してください：

```
export SLACK_BOT_TOKEN="xoxb-your-bot-token"
export SLACK_SIGNING_SECRET="your-signing-secret"
export SLACK_CLIENT_ID="your-slack-client-id"
export SLACK_CLIENT_SECRET="your-slack-client-secret"
export APP_FIREBASE_PROJECT_ID="your-project-id"
export APP_FIREBASE_CREDENTIALS_PATH="path/to/credentials.json"
```

### インストール

1. 依存パッケージのインストール:
    ```
    pip install -r functions/requirements.txt
    ```

2. Firebaseプロジェクトの初期化（未実施の場合）:
    ```
    firebase init functions
    ```

3. 設定ファイルの作成:
    - `functions/config/config.yaml` を作成し、必要な設定を記述します（slack, firebase項目など）。

### Slackアプリケーションの設定

1. [Slack API](https://api.slack.com/apps) で新しいアプリを作成
2. 以下の権限（スコープ）を追加:
   - `commands` (スラッシュコマンド使用のため)
   - `chat:write` (メッセージ送信のため)
   - `files:write` (CSVファイルアップロードのため)
   - `users:read`, `users:read.email` (ユーザー情報取得のため)
3. Slash Commandsで以下のコマンドを登録:
   - `/punch_in`
   - `/punch_out`
   - `/break_begin`
   - `/break_end`
   - `/summary`
   
   コマンドのRequest URLにはデプロイ後のエンドポイントURLを指定します。

### デプロイ

```
firebase deploy --only functions
```

デプロイ後、Slackアプリ設定の「OAuth & Permissions」でリダイレクトURLや「Interactivity & Shortcuts」「Slash Commands」のURLを更新して動作確認してください。

## 開発・テスト

### ローカルでの実行

ローカルで実行するには、functionsディレクトリ内で適宜Flask/Functions Frameworkを立ち上げ、ngrokなどでSlackからアクセス可能なURLを割り当ててください。詳細なローカルテスト手順は今後追記予定です。

## プロジェクト構造（functionsディレクトリ構成）

```
attendance-slack-bot/
├── .firebaserc
├── .gitignore
├── firestore.rules
├── functions/
│   ├── attendance/
│   │   ├── .gitignore
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── schema.py
│   ├── config/
│   │   ├── check_config.py
│   │   └── config.yaml
│   ├── src/
│   │   ├── models/
│   │   │   └── attendance.py
│   │   ├── repositories/
│   │   │   └── firestore_repository.py
│   │   ├── services/
│   │   │   ├── attendance_service.py
│   │   │   └── monthly_summary_service.py
│   │   ├── slack/
│   │   │   ├── commands/
│   │   │   │   ├── attendance_commands.py
│   │   │   │   └── summary_commands.py
│   │   │   ├── store/
│   │   │   │   ├── firestore_installation_store.py
│   │   │   │   └── firestore_state_store.py
│   │   │   ├── app.py
│   │   │   ├── message_builder.py
│   │   │   └── oauth.py
│   │   ├── utils/
│   │   │   └── time_utils.py
│   │   ├── config.py
│   │   └── main.py
│   ├── main.py
│   └── requirements.txt
└── README.md
```