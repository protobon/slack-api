from flask import Flask, request, jsonify
from slackeventsapi import SlackEventAdapter
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from os import getenv
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(getenv("SIGNIN_SECRET"), "/slack/events", app)
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
    # If the incoming message contains "hi", then respond with a "Hello" message
    if message.get("subtype") is None and "hi" in message.get('text'):
        channel = message["channel"]
        message = "Hello <@%s>! :tada:" % message["user"]
        client.chat_postMessage(channel=channel, text=message)


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


if __name__ == "__main__":
    app.run(port=3000)
