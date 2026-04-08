import boto3
import json

# Specify your AWS profile
session = boto3.Session(profile_name='int')

# Create Bedrock client
bedrock = session.client(
    service_name='bedrock-runtime',
    region_name='us-west-2'  # or your preferred region
)

# Prepare the request
prompt = "Hello! Please introduce yourself."

body = json.dumps({
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 1024,
    "messages": [
        {
            "role": "user",
            "content": prompt
        }
    ]
})

# Call Claude via Bedrock
response = bedrock.invoke_model(
    modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',  # or other Claude model
    body=body
)

# Parse and print response
response_body = json.loads(response['body'].read())
print(response_body['content'][0]['text'])
