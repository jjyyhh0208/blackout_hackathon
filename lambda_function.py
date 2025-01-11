import json
import os
import logging
from slack_client import SlackClient
from claude_client import ClaudeClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# 클라이언트 초기화
SLACK_TOKEN = os.environ["SLACK_BOT_TOKEN"]
slack_client = SlackClient(SLACK_TOKEN)
claude_client = ClaudeClient()


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        print(f"Received event body: {body}")

        event_data = slack_client.handle_event(body)
        print(f"Event data: {event_data}")

        if (
            event_data.get("type") == "message"
            and "subtype" not in event_data
            and event_data.get("bot_id") is None  # 봇 메시지 체크
            and "bot_profile" not in event_data  # 봇 프로필 체크 추가
        ):
            channel_id = event_data["channel"]
            user_id = event_data["user"]
            message = event_data["text"]
            print(f"Received message: {message}")

            # 더 많은 대화 히스토리 가져오기
            history = slack_client.get_conversation_history(channel_id, limit=5)
            history = history[::-1]
            user_chat = []
            assistant_chat = []
            for chat in history:
                if "client_msg_id" in chat:
                    user_chat.append(chat["text"])
                elif "bot_id" in chat:
                    assistant_chat.append(chat["text"])

            # user_chat, assistant_chat 리스트가 존재한다고 가정
            conversation_lines = []
            for u, a in zip(user_chat, assistant_chat):
                conversation_lines.append(f"User: {u}")
                conversation_lines.append(f"Assistant: {a}")

            conversation_text = "\n".join(conversation_lines)
            print(f"Conversation text: {conversation_text}")

        return {"statusCode": 200, "body": json.dumps({"message": "Success"})}

    except Exception as e:
        logger.error(f"에러 발생: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
