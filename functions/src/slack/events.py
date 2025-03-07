def handle_bot_invited_to_channel(event, client, logger):
    """
    Bot自身がチャンネルに追加された際に、自動で使い方とガイドサイトを案内する。
    Slack APIの `auth.test` で取得した bot_user_id と
    event["user"] のIDが一致したら、ボットが追加されたと判断する。
    """
    try:
        auth_result = client.auth_test()
        bot_user_id = auth_result["user_id"]

        # joined_user が bot_user_id と一致＝Bot自身がチャンネルに招待された
        if event.get("user") == bot_user_id:
            usage_instructions = (
                "こんにちは！チャンネルにBotを追加していただきありがとうございます。\n\n"
                "▼ まずはこちらのガイドサイトもご参照ください：\n"
                "<https://aerial-lentil-c95.notion.site/bot-164d7101a27680d98fbae0385153a637>\n\n"
                "▼ 簡単な使い方はこちら：\n"
                "- `/punch_in`: 出勤\n"
                "- `/punch_out`: 退勤\n"
                "- `/break_begin`: 休憩開始\n"
                "- `/break_end`: 休憩終了\n"
                "- `/summary`: 勤怠サマリー\n"
                "- `/allstatus`: 従業員の勤怠状況一覧\n"
                "- `/mystatus`: 自分の勤怠状況確認\n"
                "- `/help`: 使い方ガイドの表示\n\n"
                "ご不明点があればお気軽にメンションしてください！"
            )
            client.chat_postMessage(
                channel=event["channel"],
                text=usage_instructions
            )
    except Exception as e:
        logger.error(f"Error in handle_bot_invited_to_channel: {e}")