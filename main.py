## this bot needs permissions below:
# channels:history,channels:join,channels:read

import os
import csv
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# 環境変数からSLACK_BOT_TOKENを取得する
SLACK_BOT_TOKEN = None

def load_token():
    load_dotenv()
    # 環境変数からSLACK_BOT_TOKENを取得する
    global SLACK_BOT_TOKEN
    SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

    # SLACK_BOT_TOKENが設定されていない場合はエラーを出力して終了する
    if not SLACK_BOT_TOKEN:
        print("SLACK_BOT_TOKENが設定されていません")
        exit()

# チャネル一覧を取得する関数
def get_channels():
    client = WebClient(token=SLACK_BOT_TOKEN)
    channels = []
    cursor = None
    while True:
        try:
            response = client.conversations_list(
                limit=1000,
                cursor=cursor,
                types="public_channel" # ",private_channel"
            )
            channels += response["channels"]
            cursor = response["response_metadata"].get("next_cursor")
            if not cursor:
                break
        except SlackApiError as e:
            print("Error:", e)
            break
    return channels

# 発言一覧を取得する関数
def get_channel_history(channel_id, limit=100):
    client = WebClient(token=SLACK_BOT_TOKEN)
    messages = []
    oldest = 0
    while True:
        try:
            response = client.conversations_history(
                channel=channel_id,
                limit=limit,
                oldest=oldest
            )
            messages += response["messages"]
            if not response["has_more"]:
                break
            oldest = messages[-1]["ts"]
        except SlackApiError as e:
            if e.response["error"] == "not_in_channel":
                # botはチャネルに入っていないとメッセージを取得できないので入る
                response = client.conversations_join(channel=channel_id)
                print("joined slack channel:", channel_id)
                continue
            print("Error:", e)
            break
    return messages

# CSVファイルに書き出す関数
def write_csv(data, filename):
    with open(filename, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for row in data:
            writer.writerow(row)

def main():
    load_token()
    # チャネルと発言の一覧を取得する
    channels = get_channels()
    messages = []

    for channel in channels:
        channel_id = channel["id"]
        channel_name = channel["name"]
        channel_history = get_channel_history(channel_id)
        for message in channel_history:
            text = message.get("text", "")
            ts = message.get("ts", "")
            messages.append([channel_name, text, ts])

    # CSVファイルに書き出す
    write_csv(messages, "slack_messages.csv")

if __name__ == "__main__":
    main()
