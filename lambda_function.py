import json
import os
import logging
from slack_client import SlackClient
from claude_client import ClaudeClient
from mongodb_client import MongoDBClient
from data import final_info

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# 클라이언트 초기화
SLACK_TOKEN = os.environ["SLACK_BOT_TOKEN"]
MONGO_URI = os.environ["MONGO_URI"]
MONGO_DB_NAME = os.environ["MONGO_DB_NAME"]

slack_client = SlackClient(SLACK_TOKEN)
claude_client = ClaudeClient()
mongodb_client = MongoDBClient(MONGO_URI, MONGO_DB_NAME)


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        print(f"Received event body: {body}")

        event_data = slack_client.handle_event(body)
        print(f"Event data: {event_data}")

        # 여기에 봇 메시지 체크 추가
        if (
            "bot_id" in event_data
            or "bot_profile" in event_data
            or event_data.get("type") != "message"
        ):
            print("Bot message ignored")
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Bot message ignored"}),
            }

        if event_data.get("type") == "message" and "subtype" not in event_data:
            channel_id = event_data["channel"]
            message = event_data["text"]
            print(f"Received message: {message}")

            # 더 많은 대화 히스토리 가져오기
            # history = slack_client.get_conversation_history(channel_id, limit=5)
            # history = history[::-1]
            # user_chat = []
            # assistant_chat = []
            # for chat in history:
            #     if "client_msg_id" in chat:
            #         user_chat.append(chat["text"])
            #     elif "bot_id" in chat:
            #         assistant_chat.append(chat["text"])

            # # user_chat, assistant_chat 리스트가 존재한다고 가정
            # conversation_lines = []
            # for u, a in zip(user_chat, assistant_chat):
            #     conversation_lines.append(f"User: {u}")
            #     conversation_lines.append(f"Assistant: {a}")
            # conversation_lines.append(f"User: {message}")

            # conversation_text = "\n".join(conversation_lines)
            # print(f"Conversation text: {conversation_text}")

            # 대화 히스토리 없이 현재 메시지만 사용
            conversation_text = f"User: {message}"
            print(f"Conversation text: {conversation_text}")

            purpose_prompt = claude_client.form_purpose_prompt(conversation_text)
            print(f"Purpose extract prompt: {purpose_prompt}")

            user_purpose = claude_client.get_response(purpose_prompt)

            print(f"User purpose: {user_purpose}")

            final_info_text = str(final_info)

            main_prompt = claude_client.create_main_prompt(
                user_purpose, final_info=final_info_text
            )
            print(f"Main prompt: {main_prompt}")

            main_response = claude_client.get_response(main_prompt)
            print(f"Main response: {main_response}")
            if main_response:
                slack_client.send_message(channel_id, main_response)
                return {
                    "statusCode": 200,
                    "headers": {
                        "Content-Type": "application/json",
                    },
                    "body": json.dumps({"message": "Success"}),
                }

    except Exception as e:
        logger.error(f"에러 발생: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
