# 自動警告機能

自動警告機能は、長時間勤務または長時間休憩を検出し、ユーザーに自動的に警告を送信する機能です。

## 機能概要

- 長時間勤務の警告：一定時間以上連続で勤務しているユーザーに警告
- 長時間休憩の警告：一定時間以上連続で休憩しているユーザーに警告
- 設定可能な閾値：勤務・休憩の警告閾値はYAML設定ファイルで設定可能
- 自動チェック：Cloud Schedulerによる定期実行（デフォルト30分間隔）

## 設定方法

`functions/config/config.yaml` ファイルの `attendance_alerts` セクションで設定できます：

```yaml
attendance_alerts:
  enabled: true                    # 警告機能の有効/無効
  long_work_warning_minutes: 480   # 長時間勤務の警告閾値（分）
  long_break_warning_minutes: 60   # 長時間休憩の警告閾値（分）
  check_interval_minutes: 30       # チェック間隔（分）
```

- `enabled`: 警告機能全体の有効/無効を切り替えます
- `long_work_warning_minutes`: 勤務時間がこの値（分）を超えると警告します（デフォルト: 8時間）
- `long_break_warning_minutes`: 休憩時間がこの値（分）を超えると警告します（デフォルト: 1時間）
- `check_interval_minutes`: Cloud Schedulerでチェックを実行する間隔（分）

## デプロイ方法

警告機能をデプロイするには、以下の手順に従います：

1. 設定ファイルを編集（必要に応じて）
   ```bash
   nano functions/config/config.yaml
   ```

2. Firebase Functionsをデプロイ
   ```bash
   firebase deploy --only functions
   ```

3. Cloud Schedulerのジョブを作成（初回のみ）
   ```bash
   gcloud scheduler jobs create http attendance-alerts-job \
     --schedule="*/30 * * * *" \
     --uri="https://[REGION]-[PROJECT_ID].cloudfunctions.net/attendance_alerts_function" \
     --http-method=GET \
     --oidc-service-account-email=[SERVICE_ACCOUNT_EMAIL]
   ```
   - `[REGION]`: デプロイリージョン（例: `us-central1`）
   - `[PROJECT_ID]`: Firebaseプロジェクトのプロジェクトid
   - `[SERVICE_ACCOUNT_EMAIL]`: 関数を呼び出すサービスアカウント（例: `project-id@appspot.gserviceaccount.com`）

## 警告メッセージの例

### 長時間勤務の警告メッセージ

```
🚨 長時間勤務の警告

@ユーザー名 さんが 8時間30分 以上勤務しています。

必要に応じて休憩を取るか、退勤を促してください。

現在の時刻: 2023-05-01 17:30:00
```

### 長時間休憩の警告メッセージ

```
☕ 長時間休憩の警告

@ユーザー名 さんが 1時間15分 以上休憩中です。

休憩終了の処理を忘れていないか確認してください。

現在の時刻: 2023-05-01 13:45:00
```

## トラブルシューティング

### 警告が送信されない場合

1. 機能が有効になっているか確認する
   ```yaml
   attendance_alerts:
     enabled: true  # これがtrueになっているか確認
   ```

2. Cloud Schedulerのジョブが正しく設定されているか確認する
   - Google Cloud Consoleで Cloud Scheduler のセクションを確認
   - 最後の実行ステータスが成功していることを確認

3. 関数のログを確認する
   - Firebase ConsoleまたはGoogle Cloud Consoleでログを確認
   - `Running attendance alerts check...` のメッセージが定期的に表示されるはず

4. 閾値が適切に設定されているか確認する
   - 現在の閾値では検出されないケースが考えられるため、テスト用に閾値を低く設定してテスト