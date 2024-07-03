from flask import Flask, request, Response, jsonify
from slackeventsapi import SlackEventAdapter
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from os import getenv
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(getenv("SLACK_SIGNIN_SECRET"),
                                        "/slack/events",
                                        app)
client = WebClient(getenv("SLACK_TOKEN"))


def list_public_channels():
    try:
        response = client.conversations_list(
            types="public_channel"
        )
        return response["channels"]
    except SlackApiError as e:
        print(f"Error fetching channels: {e.response['error']}")
        return []


print(channel["name"] for channel in list_public_channels())


def invite_bot_to_channel(channel_id):
    try:
        response = client.conversations_join(
            channel=channel_id
        )
        return response["ok"]
    except SlackApiError as e:
        print(f"Error inviting bot to channel {channel_id}: {e.response['error']}")
        return False


def invite_bot_to_all_channels():
    channels = list_public_channels()
    for channel in channels:
        channel_id = channel["id"]
        channel_name = channel["name"]
        if invite_bot_to_channel(channel_id):
            print(f"Successfully invited bot to #{channel_name} ({channel_id})")
        else:
            print(f"Failed to invite bot to #{channel_name} ({channel_id})")


invite_bot_to_all_channels()


@slack_event_adapter.on("app_mention")
def handle_mentions(event_data):
    print(event_data)
    event = event_data["event"]
    client.chat_postMessage(
        channel=event["channel"],
        text=f"You said:\n>{event['text']}",
    )


# Example responder to greetings
@slack_event_adapter.on("message")
def handle_message(event_data):
    print(event_data)
    message = event_data["event"]
    if message.get("subtype") is None:
        channel = message["channel"]
        text = message.get("text", "").strip().lower()
    else:
        return
    if text == "hi":
        response = "Hello <@%s>! :tada:" % message["user"]
        client.chat_postMessage(channel=channel, text=response)
    if text == "help":
        response = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "This is *bold* \n"
                            "This is _italic_ \n"
                            "This is ~strikethrough~ \n"
                            "This is `code` \n"
                            "```This is a code block\nAnd it's multi-line```"
                }
            }
        ]
        client.chat_postMessage(channel=channel, blocks=response)


# Example reaction emoji echo
@slack_event_adapter.on("reaction_added")
def reaction_added(event_data):
    print(event_data)
    event = event_data["event"]
    emoji = event["reaction"]
    channel = event["item"]["channel"]
    text = ":%s:" % emoji
    client.chat_postMessage(channel=channel, text=text)


# Error events
@slack_event_adapter.on("error")
def error_handler(err):
    print("ERROR: " + str(err))


# Slash commands
@app.post("/users")
def list_users():
    try:
        data = request.form
        channel = f"#{data.get('channel_name')}"
        response = client.users_list()
        message = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Users in this workspace:\n"
                }
            }
        ]
        for user in response.data["members"]:
            message[0]["text"]["text"] += f"- {user['real_name']}\n"
        client.chat_postMessage(channel=channel, text="list of users", blocks=message)
        return Response(), 200
    except SlackApiError as e:
        print(f"Error getting list of users: {e.response['error']}")


@app.post("/codebase")
def send_codebase():
    try:
        data = request.form
        channel = f"#{data.get('channel_name')}"
        with open("main.py", "rb") as f:
            new_file = client.files_upload_v2(
                title="My codebase",
                filename="main.py",
                content=f.read()
            )
            file_url = new_file.get("file").get("permalink")
            client.chat_postMessage(channel=channel, text=f"Here's the file: {file_url}")
        return Response(), 200
    except SlackApiError as e:
        print(f"Error sending codebase file: {e.response['error']}")


if __name__ == "__main__":
    app.run(port=3000)
