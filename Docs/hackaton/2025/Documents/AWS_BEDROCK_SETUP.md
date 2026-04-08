# AWS Bedrock Setup for AI-Powered CloudFormation Conversion

## Overview
Amazon Bedrock provides access to foundation models including Claude, which can be used for CloudFormation to Terraform conversion without needing separate API keys.

## Setting Up AWS Bedrock Access

### 1. AWS Credentials
You'll need AWS credentials with Bedrock permissions. Here are the options:

#### Option A: Use Your Existing AWS Account
```bash
# If you already have AWS CLI configured (you do, since you're reading CF templates)
aws sts get-caller-identity

# Your existing credentials should work if you have Bedrock permissions
```

#### Option B: Request Bedrock Access from SkyTouch IT/DevOps
Contact your IT/DevOps team to:
- Enable Bedrock service in your AWS account
- Add Bedrock permissions to your existing IAM role/user
- Request access to Claude models in Bedrock

#### Option C: Check Your Current Permissions
```bash
# Test if you have Bedrock access
aws bedrock list-foundation-models --region us-west-2
```

### 2. Required Permissions
Your AWS user/role needs these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:ListFoundationModels",
                "bedrock:GetFoundationModel"
            ],
            "Resource": "*"
        }
    ]
}
```

### 3. Enable Claude in Bedrock Console

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Navigate to "Model access" in the left sidebar
3. Click "Request model access"
4. Enable access to Claude models:
   - Claude 3.5 Sonnet
   - Claude 3 Haiku
   - Claude 3 Sonnet

## Using Bedrock with the CF→TF Converter

### Setup
```python
from ai_converter import AIConverter

# Initialize with Bedrock
converter = AIConverter(ai_provider="bedrock")

# Convert your CloudFormation template
result = converter.convert_template_with_ai(cf_template, stack_name)
```

### Environment Variables
```bash
# Optional: Specify AWS region for Bedrock (defaults to us-west-2)
export AWS_DEFAULT_REGION=us-west-2

# Optional: Specify which Claude model to use
export BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

### Supported Bedrock Models
- `anthropic.claude-3-5-sonnet-20241022-v2:0` (Recommended)
- `anthropic.claude-3-sonnet-20240229-v1:0`
- `anthropic.claude-3-haiku-20240307-v1:0`

## Benefits of Using Bedrock

### ✅ Advantages
- **AWS Integration**: Uses your existing AWS credentials
- **No Separate API Keys**: No need for Anthropic API keys
- **Enterprise Ready**: Built for enterprise use cases
- **Cost Control**: AWS billing and cost management
- **Regional**: Can use specific AWS regions

### 💰 Cost Considerations
- Pay per token used
- Generally cost-effective for occasional use
- Monitor usage through AWS Cost Explorer

## Company-Specific Notes for SkyTouch

Since you already have AWS access (you're reading CloudFormation templates), you likely just need Bedrock permissions enabled.

### Recommended Approach:
1. **Check Current Access**: Test with `aws bedrock list-foundation-models`
2. **Request Permissions**: Ask IT/DevOps to enable Bedrock access
3. **Start Small**: Test with one CloudFormation template first
4. **Scale Up**: Once working, use for batch processing

### Who to Contact at SkyTouch:
Based on the Jira issues found, these people might help with AWS access:
- **Infrastructure Team**: For AWS permissions
- **DevOps Team**: For service enablement
- **Your Manager**: For approval if needed

## Testing Your Setup

```python
#!/usr/bin/env python3
"""Test AWS Bedrock access"""

import boto3
from botocore.exceptions import ClientError

def test_bedrock_access():
    try:
        # Test AWS credentials
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Identity: {identity.get('Arn', 'Unknown')}")
        
        # Test Bedrock access
        bedrock = boto3.client('bedrock', region_name='us-west-2')
        models = bedrock.list_foundation_models()
        
        claude_models = [
            model for model in models['modelSummaries'] 
            if 'claude' in model['modelName'].lower()
        ]
        
        if claude_models:
            print(f"✅ Bedrock Access: Found {len(claude_models)} Claude models")
            for model in claude_models[:3]:
                print(f"   - {model['modelId']}")
        else:
            print("⚠️  Bedrock Access: No Claude models found")
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UnauthorizedOperation':
            print("❌ Missing Bedrock permissions")
        elif error_code == 'AccessDenied':
            print("❌ Access denied - need IAM permissions")
        else:
            print(f"❌ AWS Error: {error_code}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    test_bedrock_access()
```

## Next Steps

1. **Test Access**: Run the test script above
2. **Request Permissions**: If needed, contact SkyTouch IT/DevOps
3. **Try Conversion**: Use the updated AI converter with Bedrock
4. **Scale Usage**: Once working, integrate into your workflow

This approach leverages your existing AWS infrastructure and doesn't require separate API keys or external services.
