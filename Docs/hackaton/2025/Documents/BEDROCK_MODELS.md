# AWS Bedrock Model Selection Guide

## How to Change the Model ID

### Method 1: Environment Variable (Recommended)
```bash
# Set the model you want to use
export BEDROCK_MODEL_ID="anthropic.claude-3-haiku-20240307-v1:0"

# Then run your conversion
python test_ai_conversion.py your-profile
```

### Method 2: In Python Code
```python
import os
from ai_converter import AIConverter

# Set model before creating converter
os.environ['BEDROCK_MODEL_ID'] = 'anthropic.claude-3-haiku-20240307-v1:0'

converter = AIConverter(aws_profile="your-profile")
```

### Method 3: Modify the Code
In `ai_converter.py`, find this line:
```python
model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
```
Change the default value to your preferred model.

## How to See Available Models

### Check What Models You Have Access To
```bash
# List all available models in your account
python -c "
import boto3
session = boto3.Session(profile_name='your-profile')
bedrock = session.client('bedrock', region_name='us-west-2')
models = bedrock.list_foundation_models()

print('Available Claude Models:')
for model in models['modelSummaries']:
    if 'claude' in model['modelName'].lower():
        print(f'ID: {model[\"modelId\"]}')
        print(f'Name: {model[\"modelName\"]}')
        print(f'Provider: {model[\"providerName\"]}')
        print(f'Status: {model.get(\"modelLifecycle\", {}).get(\"status\", \"Unknown\")}')
        print('---')
"
```

### Or Use the Test Script
```bash
# The Bedrock test script also shows available models
python test_bedrock_access.py your-profile
```

## Claude Model Options in Bedrock

### Claude 3.5 Sonnet (Recommended)
```bash
export BEDROCK_MODEL_ID="anthropic.claude-3-5-sonnet-20241022-v2:0"
```
- **Best for**: Complex CloudFormation conversions
- **Pros**: Highest quality, best at understanding complex templates
- **Cons**: More expensive, slower
- **Use when**: Converting complex stacks with many resources

### Claude 3 Sonnet 
```bash
export BEDROCK_MODEL_ID="anthropic.claude-3-sonnet-20240229-v1:0"
```
- **Best for**: Most CloudFormation conversions
- **Pros**: Good balance of quality and speed
- **Cons**: Less capable than 3.5 Sonnet
- **Use when**: Standard conversions, good default choice

### Claude 3 Haiku (Fastest/Cheapest)
```bash
export BEDROCK_MODEL_ID="anthropic.claude-3-haiku-20240307-v1:0"
```
- **Best for**: Simple templates, testing, batch processing
- **Pros**: Very fast, very cheap
- **Cons**: Lower quality on complex conversions
- **Use when**: Simple stacks, testing, cost is a concern

## Model Comparison for CF→TF Conversion

| Model | Speed | Cost | Quality | Best For |
|-------|-------|------|---------|----------|
| Claude 3.5 Sonnet | Slow | High | Excellent | Complex stacks, production |
| Claude 3 Sonnet | Medium | Medium | Very Good | Most use cases |
| Claude 3 Haiku | Fast | Low | Good | Simple stacks, testing |

## How to Test Different Models

### Create a Simple Test Script
```python
#!/usr/bin/env python3
"""Test different Bedrock models"""

import os
import json
from ai_converter import AIConverter

# Test models to try
models_to_test = [
    "anthropic.claude-3-haiku-20240307-v1:0",      # Fastest/cheapest
    "anthropic.claude-3-sonnet-20240229-v1:0",     # Balanced
    "anthropic.claude-3-5-sonnet-20241022-v2:0"    # Best quality
]

def test_model(model_id, aws_profile):
    """Test a specific model with a simple CF template"""
    
    print(f"\n🧪 Testing model: {model_id}")
    
    # Set the model
    os.environ['BEDROCK_MODEL_ID'] = model_id
    
    # Simple CF template for testing
    simple_cf = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Resources": {
            "TestBucket": {
                "Type": "AWS::S3::Bucket",
                "Properties": {
                    "BucketName": "test-bucket-example"
                }
            }
        }
    }
    
    try:
        converter = AIConverter(aws_profile=aws_profile)
        result = converter.convert_template_with_ai(simple_cf, "test-stack")
        
        print(f"✅ Success! Generated {len(result['terraform_files'])} files")
        print(f"📊 Response length: {len(result['ai_response'])} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False

# Test all models
for model in models_to_test:
    test_model(model, "your-profile")
```

## Enabling Model Access

If you get "ValidationException" errors, you need to enable model access:

### In AWS Bedrock Console:
1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Click "Model access" in left sidebar  
3. Click "Request model access"
4. Enable these models:
   - ✅ Claude 3.5 Sonnet
   - ✅ Claude 3 Sonnet  
   - ✅ Claude 3 Haiku

### Via AWS CLI:
```bash
# Check current model access
aws bedrock list-foundation-models --profile your-profile --region us-west-2

# Request access to specific models (if needed)
aws bedrock put-model-invocation-logging-configuration \
    --profile your-profile \
    --region us-west-2
```

## Model Selection Recommendations

### For SkyTouch CloudFormation Conversion:

**🏁 Getting Started:**
- Start with **Claude 3 Haiku** for testing
- It's fast and cheap while you learn the system

**📈 Production Use:**
- Use **Claude 3 Sonnet** for most conversions
- Good balance of quality and cost

**🎯 Complex Stacks:**
- Use **Claude 3.5 Sonnet** for:
  - Large stacks (50+ resources)
  - Complex nested templates
  - Stacks with many conditions/functions
  - Production-critical conversions

**💰 Cost Optimization:**
- Use **Claude 3 Haiku** for:
  - Batch processing many simple stacks
  - Development/testing
  - Templates you've converted before (for updates)

## Setting Your Default Model

Add this to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
# Set your preferred Bedrock model
export BEDROCK_MODEL_ID="anthropic.claude-3-sonnet-20240229-v1:0"

# Set your Bedrock profile  
export AWS_PROFILE="your-bedrock-profile"
```

Then you can just run:
```bash
python test_ai_conversion.py
# Uses your default model and profile
```

## Troubleshooting Model Issues

### Model Not Available
```
ValidationException: The provided model identifier is invalid
```
**Solution**: Check available models and enable access in Bedrock console

### Access Denied
```
AccessDenied: User is not authorized to perform: bedrock:InvokeModel
```
**Solution**: Add `bedrock:InvokeModel` permission to your IAM role/user

### Model Not Found
```
Could not resolve the foundation model from the provided model identifier
```
**Solution**: Double-check the model ID spelling and region
