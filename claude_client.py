import json
import boto3
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class ClaudeClient:
    def __init__(self):
        self.bedrock_runtime = boto3.client("bedrock-runtime")

    def get_response(self, prompt: str) -> str:
        """대화 내용을 받아서 Claude에 요청"""
        try:
            formatted_prompt = [{"role": "user", "content": prompt}]
            body = json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1024,
                    "messages": formatted_prompt,
                    "temperature": 0.7,
                }
            )

            response = self.bedrock_runtime.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                contentType="application/json",
                body=body,
            )

            response_body = json.loads(response["body"].read())
            print(f"Response body: {response_body}")
            response_text = response_body["content"][0]["text"]

            return response_text

        except Exception as e:
            logger.error(f"Bedrock API 에러: {str(e)}")
            return "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다."

    def form_purpose_prompt(self, conversation_text: str) -> str:
        """대화 내용을 Claude 형식으로 변환"""
        conversations = conversation_text
        print(f"Conversations: {conversations}")

        prompt = f"""
        너는 교환학생을 지원하는 학생에게 조언을 해주는 컨설턴트야.
        다음 대화 내용을 보고 유저의 의도를 파악해줘.
        
        Conversation:
        '{conversations}'
        
        Conversation의 대화 목록을 보고 유저의 마지막 의도를 파악해줘.
        
        교환학생 정보에 대한 문의를 하는 학생들이 무엇을 궁금해하는지 문의들의 의도를 파악해야해.
        고객의 마지막 말의 의미와 마지막 말에 대한 고객의 핵심 문의 내용 및 상황만 설명해주고, 상담원의 행동 지침에 대해서는 절대 말하지 마.
        """
        return prompt

    def form_summary_prompt(self, category: str, review_text: str) -> str:
        prompt = f"""
        다음 category에 대한 수기들을 보고 겹치는 내용들을 제거해줘.
        
        Category:
        '{category}'
        
        Review:
        '{review_text}'
        
        절대 같은 내용을 두번 이상 쓰거나 새로운 내용을 추가해서는 안된다.
        반드시 Review에 있는 내용들을 기반으로 겹치는 내용들을 제거해야한다.
        """
        return prompt

    def create_main_prompt(self, user_purpose: str, final_info: str) -> str:
        prompt = f"""
        User purpose:
        '{user_purpose}'
        
        Final info:
        '{final_info}'
        
        위 Final info를 보고 User purpose를 파악해서 유저의 문의에 대한 정보를 제공해야해.
        반드시 제공된 정보를 기반으로 정보를 제공해야해.
        
        만약 고객이 '안녕하세요', '문의', '문의드립니다', '문의드립니다.'와 같이 의도가 불분명한 말을 하면 반드시 '안녕하세요. 무엇을 도와드릴까요?'와 같은 말을 해야해.
        
        특정 내용이 Final info에 포함되어 있지 않다는 것은, 그 내용과 무관하게 진행 가능한 것이 아니라 반드시 'https://www.uab.cat/web/mobility-international-exchange-1345680336097.html'를 제공해야함. 해당 링크는 문의 학교에 대한 홈페이지로 이동하는 링크임.
        """
        return prompt
