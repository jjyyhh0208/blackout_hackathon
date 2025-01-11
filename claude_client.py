import json
import boto3
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class ClaudeClient:
    def __init__(self):
        self.bedrock_runtime = boto3.client("bedrock-runtime")

    def get_response(self, conversation_text: str) -> str:
        """대화 내용을 받아서 Claude에 요청"""
        try:
            # Human/Assistant 형식을 Claude 형식으로 변환
            formatted_text = conversation_text.replace("User:", "Human:")

            body = json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens_to_sample": 1024,
                    "prompt": formatted_text,
                    "temperature": 0.7,
                }
            )

            response = self.bedrock_runtime.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                contentType="application/json",
                body=body,
            )

            response_body = json.loads(response["body"].read())
            return response_body["content"][0]["text"]

        except Exception as e:
            logger.error(f"Bedrock API 에러: {str(e)}")
            return "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다."
