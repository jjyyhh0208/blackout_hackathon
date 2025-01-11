import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class SlackClient:
    def __init__(self, token: str):
        self.client = WebClient(token=token)

    def handle_event(self, event_body: dict) -> dict:
        if "challenge" in event_body:
            return {
                "statusCode": 200,
                "body": json.dumps({"challenge": event_body["challenge"]}),
            }

        event_data = event_body.get("event", {})
        return event_data

    def send_message(self, channel: str, text: str) -> None:
        try:
            self.client.chat_postMessage(channel=channel, text=text)
        except SlackApiError as e:
            logger.error(f"Slack API 에러: {e.response['error']}")
            raise

    def get_conversation_history(self, channel: str, limit: int = 5) -> list:
        try:
            result = self.client.conversations_history(channel=channel, limit=limit)
            return result["messages"]
        except SlackApiError as e:
            logger.error(f"Slack API 에러: {e.response['error']}")
            return []
