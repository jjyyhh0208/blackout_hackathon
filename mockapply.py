import os
import json
import logging
from bson import ObjectId
from pymongo import MongoClient
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# 로깅 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# MongoDB 및 Slack 클라이언트 초기화
MONGO_URI = os.environ['MONGO_URI']
SLACK_TOKEN = os.environ['SLACK_BOT_TOKEN']
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['blackout_10']
exchange_school_collection = db['exchange_school']
user_data_collection = db['user_data']
event_log_collection = db['event_log']  # 이벤트 로그를 저장할 새로운 컬렉션
slack_client = WebClient(token=SLACK_TOKEN)

def is_duplicate_event(event_id):
    """
    이벤트 중복 여부 확인.

    Args:
        event_id (str): 슬랙 이벤트 ID.

    Returns:
        bool: 중복 여부.
    """
    if event_log_collection.find_one({"event_id": event_id}):
        return True
    event_log_collection.insert_one({"event_id": event_id})
    return False

def calculate_rank_for_school(school_id, score):
    """
    특정 학교에 대해 점수 순위와 전체 인원 수를 계산.

    Args:
        school_id (str): 학교 ID (ObjectId 형태).
        score (float): 현재 사용자의 점수.

    Returns:
        tuple: (현재 사용자의 등수, 전체 인원 수)
    """
    school_object_id = ObjectId(school_id)

    # 특정 학교를 포함하는 유저 필터링
    relevant_users = list(user_data_collection.find({
        "applied_schools": school_object_id
    }))

    # 점수 리스트 추출 및 정렬
    score_list = sorted(
        [user.get("score", 0.0) for user in relevant_users], reverse=True
    )

    # 현재 사용자의 등수 계산
    try:
        rank = score_list.index(score) + 1  # 1-based index
    except ValueError:
        rank = None  # 현재 사용자가 리스트에 없을 경우

    total_users = len(score_list)

    return rank, total_users

def save_user_data(name, schools, score):
    """
    유저 데이터를 저장하고 중복 여부를 확인.

    Args:
        name (str): 유저 이름.
        schools (list): 지원한 학교 리스트.
        score (float): 유저 점수.

    Returns:
        bool: 데이터가 새로 저장되었는지 여부.
    """
    existing_user = user_data_collection.find_one({
        "name": name,
        "applied_schools": {"$all": [ObjectId(s) for s in schools]},
        "score": score
    })

    if existing_user:
        logger.info("중복된 데이터로 저장하지 않습니다.")
        return False

    # 유저 데이터 저장
    user_data_collection.insert_one({
        "name": name,
        "applied_schools": [ObjectId(s) for s in schools],
        "score": score
    })
    return True

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])

        # URL 검증 처리
        if 'challenge' in body:
            return {
                'statusCode': 200,
                'body': json.dumps({'challenge': body['challenge']})
            }

        # Slack 이벤트 처리
        if 'event' in body:
            slack_event = body['event']
            event_type = slack_event.get('type')
            event_id = body.get('event_id')  # 이벤트 고유 ID 가져오기

            if event_type == 'app_mention':
                channel_id = slack_event['channel']
                user_id = slack_event['user']
                text = slack_event['text']

                # 중복 이벤트 확인
                if is_duplicate_event(event_id):
                    logger.info(f"중복된 이벤트 무시: {event_id}")
                    return {
                        'statusCode': 200,
                        'body': json.dumps({'message': 'Duplicate event ignored'})
                    }

                # 멘션(`@MockApply`)을 제외한 입력값 추출
                user_input = text.split('>', 1)[1].strip()
                if ',' not in user_input:
                    slack_client.chat_postMessage(
                        channel=channel_id,
                        text=(f"<@{user_id}> 데이터를 입력해주세요.\n"
                              "형식: 이름, 1~5순위 희망학교(쉼표로 구분), 점수")
                    )
                    return {
                        'statusCode': 200,
                        'body': json.dumps({'message': 'Guide message sent'})
                    }

                try:
                    parts = [part.strip() for part in user_input.split(',')]
                    if len(parts) != 7:
                        raise ValueError("입력값이 올바르지 않습니다. 이름, 학교 5개, 점수를 쉼표로 구분해주세요.")

                    name = parts[0]
                    schools = parts[1:6]
                    score = float(parts[6])

                    applied_school_ids = []
                    for school_name in schools:
                        school = exchange_school_collection.find_one({"university_name": school_name})
                        if school:
                            applied_school_ids.append(str(school['_id']))
                        else:
                            applied_school_ids.append(None)

                    # 유저 데이터 저장
                    data_saved = save_user_data(name, applied_school_ids, score)
                    result_message = f"<@{user_id}> 신청한 학교별 정보:\n"

                    for idx, school_id in enumerate(applied_school_ids):
                        if not school_id:
                            result_message += f"{idx + 1}순위: 학교 데이터가 없습니다.\n"
                            continue

                        school = exchange_school_collection.find_one({"_id": ObjectId(school_id)})
                        university_name = school["university_name"]
                        selection_quota = school["selection_quota"]

                        rank, total_users = calculate_rank_for_school(school_id, score)

                        if rank is None:
                            result_message += (
                                f"{idx + 1}순위: {university_name}, "
                                f"합격 인원: {selection_quota}, "
                                "등수: 계산 불가 (데이터 없음)\n"
                            )
                        else:
                            result_message += (
                                f"{idx + 1}순위: {university_name}, "
                                f"합격 인원: {selection_quota}, "
                                f"등수: {rank}/{total_users}\n"
                            )

                    slack_client.chat_postMessage(
                        channel=channel_id,
                        text=(f"<@{user_id}> 데이터가 {'저장되었습니다' if data_saved else '중복되어 저장되지 않았습니다'}:\n\n"
                              f"{result_message}")
                    )

                except ValueError as e:
                    slack_client.chat_postMessage(
                        channel=channel_id,
                        text=f"<@{user_id}> 입력 형식이 잘못되었습니다. 형식: 이름, 1~5순위 희망학교(쉼표로 구분), 점수\n오류: {str(e)}"
                    )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Event processed'})
        }

    except SlackApiError as e:
        logger.error(f"Slack API 에러: {e.response['error']}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
    except Exception as e:
        logger.error(f"에러 발생: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
