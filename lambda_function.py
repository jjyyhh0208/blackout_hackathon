import json
from test import test_bedrock_connection
from test2 import mongo

def lambda_handler(event, context):
    """
    Lambda entry point
    """
    # Parse incoming Slack command request
    test_bedrock_connection()
    mongo()

