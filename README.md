# Attendance Management Slack Bot

Firebase Functions と Slack Bolt.js を使用した勤怠管理用 Slack Bot

## 機能

- `/punch_in` - 出勤を記録
- `/punch_out` - 退勤を記録（実働時間と休憩時間を計算）
- `/break_begin` - 休憩開始を記録
- `/break_end` - 休憩終了を記録（休憩時間を計算）

## セットアップ

### 必要条件

- Python 3.8以上
- Firebase CLIツール
- Slackワークスペースの管理者権限

### 環境変数の設定

以下の環境変数を設定してください：

```bash
export SLACK_BOT_TOKEN="xoxb-your-bot-token"
export SLACK_SIGNING_SECRET="your-signing-secret"
export FIREBASE_PROJECT_ID="your-project-id"
export FIREBASE_CREDENTIALS_PATH="path/to/credentials.json"
```

### インストール

1. 依存パッケージのインストール:
```bash
pip install -r requirements.txt
```

2. Firebaseプロジェクトの初期化:
```bash
firebase init functions
```

3. 設定ファイルの作成:
- `config/config.yaml` を作成し、必要な設定を記述

### Slackアプリケーションの設定

1. [Slack API](https://api.slack.com/apps) で新しいアプリケーションを作成
2. 以下の権限を追加:
   - `commands` - Slackコマンドの使用
   - `chat:write` - メッセージの送信
3. Slash Commandsの設定:
   - `/punch_in`
   - `/punch_out`
   - `/break_begin`
   - `/break_end`

### デプロイ

```bash
firebase deploy --only functions
```

## 開発

### ローカルでの実行

```bash
python src/main.py
```

## プロジェクト構造

```
attendance-slack-bot/
├── config/
│   └── config.yaml       # アプリケーション設定
├── src/
│   ├── models/          # データモデル
│   ├── repositories/    # データアクセス層
│   ├── services/        # ビジネスロジック
│   ├── slack/           # Slack関連の実装
│   └── utils/           # ユーティリティ関数
├── tests/               # テストコード(今後作成)
├── requirements.txt     # 依存パッケージ
└── README.md           # このファイル
```

## ライセンス
(今後記述)