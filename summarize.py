import boto3
import json

client = boto3.client("bedrock-runtime", region_name="us-east-1")

prompt = "What is the significance of cloud computing?"

kwargs = {
    "modelId": "meta.llama3-8b-instruct-v1:0",
    "contentType": "application/json",
    "accept": "application/json",
    "body": json.dumps({"prompt": prompt}),
}

response = client.invoke_model(**kwargs)
print(json.loads(response["body"].read()))
