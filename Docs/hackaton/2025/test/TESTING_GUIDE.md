# Testing the AI Converter - Complete Guide

## Quick Test Commands

### 1. Test Bedrock Access First
```bash
# Test if your profile can access Bedrock
python test_bedrock_access.py your-bedrock-profile
```

### 2. Test AI Conversion with Real Template
```bash
# Use your cached CloudFormation templates
python test_ai_conversion.py your-bedrock-profile
```

### 3. List Available Models
```bash
# See what models you have access to
python list_bedrock_models.py your-bedrock-profile
```

## Step-by-Step Testing Process

### Step 1: Verify Prerequisites
```bash
# Check you have the required Python packages
python -c "import boto3, yaml, colorama; print('✅ All packages available')"

# Check your AWS profiles
aws configure list-profiles

# Check your cached templates
ls -la ../cf_templates_cache/
```

### Step 2: Test Bedrock Connection
```bash
# Test with your Bedrock profile
python test_bedrock_access.py your-bedrock-profile

# Should show:
# ✅ AWS Identity: arn:aws:iam::...
# ✅ Bedrock service accessible
# ✅ Found X Claude models
# ✅ Bedrock Runtime works!
```

### Step 3: Test Model Selection
```bash
# See your available models
python list_bedrock_models.py your-bedrock-profile

# Try a fast model for testing
export BEDROCK_MODEL_ID="anthropic.claude-3-haiku-20240307-v1:0"
python list_bedrock_models.py your-bedrock-profile test
```

### Step 4: Test Full Conversion
```bash
# Run full conversion test
python test_ai_conversion.py your-bedrock-profile

# Should create files in ./ai_output/
```

## Manual Testing with Python

### Basic AI Converter Test
```python
#!/usr/bin/env python3
"""Manual test of AI converter"""

from ai_converter import AIConverter
import json

# Simple CloudFormation template for testing
test_template = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Description": "Test template for AI converter",
    "Resources": {
        "TestBucket": {
            "Type": "AWS::S3::Bucket",
            "Properties": {
                "BucketName": "my-test-bucket",
                "Tags": [
                    {"Key": "app_name", "Value": "test-app"},
                    {"Key": "environment", "Value": "INT"},
                    {"Key": "app_environment_id", "Value": "int03"}
                ]
            }
        }
    },
    "Outputs": {
        "BucketName": {
            "Description": "Name of the S3 bucket",
            "Value": {"Ref": "TestBucket"}
        }
    }
}

def test_ai_converter():
    """Test the AI converter with a simple template"""
    
    print("🧪 Testing AI Converter...")
    
    # Initialize converter
    converter = AIConverter(aws_profile="your-bedrock-profile")
    
    # Convert template
    result = converter.convert_template_with_ai(test_template, "TEST-STACK")
    
    # Check results
    print(f"✅ Generated {len(result['terraform_files'])} files:")
    for filename in result['terraform_files'].keys():
        print(f"  📄 {filename}")
    
    # Save results
    output_path = converter.save_conversion(result, "./test_output")
    print(f"📁 Results saved to: {output_path}")
    
    return result

if __name__ == '__main__':
    test_ai_converter()
```

### Test Different Models
```python
#!/usr/bin/env python3
"""Test different Bedrock models"""

import os
from ai_converter import AIConverter

# Models to test (fastest to slowest)
models = [
    "anthropic.claude-3-haiku-20240307-v1:0",      # Fast
    "anthropic.claude-3-sonnet-20240229-v1:0",     # Balanced  
    "anthropic.claude-3-5-sonnet-20241022-v2:0"    # Best
]

simple_template = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Resources": {
        "TestBucket": {
            "Type": "AWS::S3::Bucket",
            "Properties": {"BucketName": "test-bucket"}
        }
    }
}

def test_model(model_id, aws_profile):
    """Test a specific model"""
    
    print(f"\n🧪 Testing: {model_id}")
    
    # Set model
    os.environ['BEDROCK_MODEL_ID'] = model_id
    
    try:
        converter = AIConverter(aws_profile=aws_profile)
        result = converter.convert_template_with_ai(simple_template, "test")
        
        print(f"  ✅ Success!")
        print(f"  📊 Files: {len(result['terraform_files'])}")
        print(f"  📏 Response: {len(result['ai_response'])} chars")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed: {str(e)}")
        return False

# Test all models
for model in models:
    test_model(model, "your-bedrock-profile")
```

## Troubleshooting Tests

### Test 1: Import Check
```python
# Check if ai_converter imports correctly
try:
    from ai_converter import AIConverter
    print("✅ AI converter imports successfully")
except Exception as e:
    print(f"❌ Import error: {e}")
```

### Test 2: AWS Credentials
```python
# Check AWS credentials work
import boto3
try:
    session = boto3.Session(profile_name='your-bedrock-profile')
    sts = session.client('sts')
    identity = sts.get_caller_identity()
    print(f"✅ AWS credentials work: {identity['Arn']}")
except Exception as e:
    print(f"❌ AWS error: {e}")
```

### Test 3: Bedrock Access
```python
# Test Bedrock specifically
import boto3
try:
    session = boto3.Session(profile_name='your-bedrock-profile')
    bedrock = session.client('bedrock', region_name='us-west-2')
    models = bedrock.list_foundation_models()
    print(f"✅ Bedrock works: {len(models['modelSummaries'])} models")
except Exception as e:
    print(f"❌ Bedrock error: {e}")
```

### Test 4: Model Invocation
```python
# Test actual model call
import boto3, json
try:
    session = boto3.Session(profile_name='your-bedrock-profile')
    bedrock_runtime = session.client('bedrock-runtime', region_name='us-west-2')
    
    response = bedrock_runtime.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 20,
            "messages": [{"role": "user", "content": "Say hello"}]
        })
    )
    
    result = json.loads(response['body'].read())
    print(f"✅ Model works: {result['content'][0]['text']}")
except Exception as e:
    print(f"❌ Model error: {e}")
```

## Common Test Scenarios

### Scenario 1: Test with Your Real CloudFormation Template
```bash
# Use your existing cached template
cd cf-to-tf-converter
python test_ai_conversion.py your-bedrock-profile

# Check output
ls -la ai_output/*/
cat ai_output/*/main.tf
```

### Scenario 2: Test with Different Stack Types
```python
# Test with EC2 resources
ec2_template = {
    "Resources": {
        "MyInstance": {
            "Type": "AWS::EC2::Instance", 
            "Properties": {
                "InstanceType": "t3.micro",
                "ImageId": "ami-12345"
            }
        }
    }
}

# Test with RDS resources  
rds_template = {
    "Resources": {
        "MyDB": {
            "Type": "AWS::RDS::DBInstance",
            "Properties": {
                "DBInstanceClass": "db.t3.micro",
                "Engine": "mysql"
            }
        }
    }
}
```

### Scenario 3: Test Error Handling
```python
# Test with invalid model ID
os.environ['BEDROCK_MODEL_ID'] = 'invalid-model-id'
# Should gracefully fail and create prompt file

# Test with empty template
empty_template = {}
# Should handle gracefully

# Test without Bedrock access
# Should fallback to prompt mode
```

## Expected Test Results

### Successful Test Should Show:
```
🤖 AI-powered conversion starting for: TEST-STACK
🔧 Using AWS profile: your-bedrock-profile  
✅ AI conversion completed for: TEST-STACK
✅ AI conversion results saved to: ./ai_output/TEST-STACK
  📄 Terraform files: 5
  📊 Conversion report: ai_conversion_report.json
  🤖 AI prompt: ai_prompt.txt
  📝 Raw response: ai_response_raw.txt
```

### Generated Files Should Include:
- `main.tf` - Main Terraform configuration
- `variables.tf` - Variable definitions  
- `outputs.tf` - Output definitions
- `provider.tf` - Provider configuration
- `terraform.tfvars.example` - Example variables
- `ai_conversion_report.json` - Conversion metadata
- `ai_prompt.txt` - Original prompt sent to AI
- `ai_response_raw.txt` - Full AI response

## Performance Testing

### Test Response Times
```python
import time
from ai_converter import AIConverter

def time_conversion(template, model_id, aws_profile):
    """Time how long conversion takes"""
    
    os.environ['BEDROCK_MODEL_ID'] = model_id
    converter = AIConverter(aws_profile=aws_profile)
    
    start_time = time.time()
    result = converter.convert_template_with_ai(template, "perf-test")
    end_time = time.time()
    
    duration = end_time - start_time
    chars = len(result['ai_response'])
    
    print(f"Model: {model_id}")
    print(f"Time: {duration:.2f} seconds")
    print(f"Response: {chars} characters")
    print(f"Rate: {chars/duration:.1f} chars/sec")
    
    return duration
```

## Validation Testing

### Validate Terraform Output
```bash
# After conversion, validate the generated Terraform
cd ai_output/your-stack-name

# Check syntax
terraform fmt -check

# Validate configuration  
terraform init -backend=false
terraform validate

# Plan (will show what would be created)
terraform plan
```

This comprehensive testing approach ensures your AI converter works correctly with your Bedrock setup!
