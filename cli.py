import cmd
from slack_sdk import WebClient
from os import getenv
from dotenv import load_dotenv

load_dotenv()
client = WebClient(getenv("SLACK_TOKEN"))


class SlackCLI(cmd.Cmd):
    prompt = "(slack): "
    intro = "Welcome to the Slack CLI. Type 'help' to list available commands"

    @staticmethod
    def do_message(line):
        """ Sends a message to a Slack channel. Usage: message #channel text """
        try:
            args = line.split(" ", 1)
            if len(args) != 2:
                print("usage: message #channel text")
            channel, text = args
            if not channel.startswith('#'):
                print("Channel name should start with '#'")
                return
            client.chat_postMessage(channel=channel, text=text)
            print(f"Message sent")
        except Exception as e:
            print(e)


if __name__ == "__main__":
    SlackCLI().cmdloop()
