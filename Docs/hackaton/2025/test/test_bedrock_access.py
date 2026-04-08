#!/usr/bin/env python3
"""
Test AWS Bedrock Access for CloudFormation to Terraform Conversion
Simple script to verify Bedrock permissions before running conversion
"""

import boto3
import json
from botocore.exceptions import ClientError
from colorama import Fore, Style, init

init()

def test_bedrock_access(aws_profile: str = None):
    """Test if we can access AWS Bedrock with current credentials"""
    
    print(f"{Fore.CYAN}🔍 Testing AWS Bedrock Access{Style.RESET_ALL}")
    if aws_profile:
        print(f"🔧 Using AWS profile: {aws_profile}")
    print("=" * 50)
    
    try:
        # Test basic AWS credentials
        print("1. Testing AWS credentials...")
        
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
            sts = session.client('sts')
        else:
            sts = boto3.client('sts')
            
        identity = sts.get_caller_identity()
        
        print(f"   ✅ AWS Identity: {identity.get('Arn', 'Unknown')}")
        print(f"   ✅ Account ID: {identity.get('Account', 'Unknown')}")
        
        # Test Bedrock service access
        print("\n2. Testing Bedrock service access...")
        
        if aws_profile:
            bedrock = session.client('bedrock', region_name='us-west-2')
        else:
            bedrock = boto3.client('bedrock', region_name='us-west-2')
        
        try:
            models = bedrock.list_foundation_models()
            print(f"   ✅ Bedrock service accessible")
            
            # Find Claude models
            claude_models = [
                model for model in models['modelSummaries'] 
                if 'claude' in model['modelName'].lower()
            ]
            
            if claude_models:
                print(f"   ✅ Found {len(claude_models)} Claude models:")
                for model in claude_models[:3]:
                    print(f"      - {model['modelId']}")
                    print(f"        Status: {model.get('modelLifecycle', {}).get('status', 'Unknown')}")
            else:
                print(f"   ⚠️  No Claude models found")
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                print(f"   ❌ Bedrock access denied")
                print(f"   💡 You need Bedrock permissions added to your IAM role/user")
                return False
            else:
                raise
        
        # Test Bedrock Runtime (for actual AI calls)
        print("\n3. Testing Bedrock Runtime access...")
        
        if aws_profile:
            bedrock_runtime = session.client('bedrock-runtime', region_name='us-west-2')
        else:
            bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-west-2')
        
        # Try a simple test call with Claude
        model_id = 'anthropic.claude-3-haiku-20240307-v1:0'  # Use fast/cheap model for test
        
        test_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 50,
            "messages": [
                {
                    "role": "user",
                    "content": "Say 'Bedrock test successful' in exactly 3 words."
                }
            ]
        }
        
        try:
            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(test_body)
            )
            
            response_body = json.loads(response['body'].read())
            
            if 'content' in response_body:
                ai_response = response_body['content'][0]['text']
                print(f"   ✅ Bedrock Runtime works!")
                print(f"   🤖 Test AI Response: {ai_response.strip()}")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                print(f"   ❌ Bedrock Runtime access denied")
                print(f"   💡 You need bedrock:InvokeModel permission")
                return False
            elif error_code == 'ValidationException':
                print(f"   ⚠️  Model not available: {model_id}")
                print(f"   💡 You may need to enable model access in Bedrock console")
                return False
            else:
                raise
        
        print(f"\n{Fore.GREEN}🎉 Bedrock Access Test: SUCCESS!{Style.RESET_ALL}")
        print(f"✅ You can now use the CF→TF converter with Bedrock")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        
        if error_code == 'UnauthorizedOperation':
            print(f"   ❌ Missing AWS permissions")
        elif error_code == 'AccessDenied':
            print(f"   ❌ Access denied - check IAM permissions")
        else:
            print(f"   ❌ AWS Error: {error_code}")
            print(f"   📝 Details: {e.response['Error'].get('Message', 'Unknown')}")
        
        return False
        
    except Exception as e:
        print(f"   ❌ Unexpected error: {str(e)}")
        return False

def show_bedrock_setup_help():
    """Show help for setting up Bedrock access"""
    
    print(f"\n{Fore.YELLOW}📋 Bedrock Setup Help{Style.RESET_ALL}")
    print("=" * 30)
    print()
    print("If the test failed, here's what you need:")
    print()
    print("1. 📝 Required IAM Permissions:")
    print("   - bedrock:ListFoundationModels")
    print("   - bedrock:InvokeModel")
    print("   - bedrock:GetFoundationModel")
    print()
    print("2. 🌐 Enable Model Access:")
    print("   - Go to AWS Bedrock Console")
    print("   - Navigate to 'Model access'") 
    print("   - Request access to Claude models")
    print()
    print("3. 👥 Who to Contact at SkyTouch:")
    print("   - IT/DevOps team for IAM permissions")
    print("   - Infrastructure team for Bedrock enablement")
    print()
    print("4. 📚 More Details:")
    print("   - See AWS_BEDROCK_SETUP.md for complete setup guide")

if __name__ == '__main__':
    import sys
    
    # Check for profile argument
    aws_profile = None
    if len(sys.argv) > 1:
        aws_profile = sys.argv[1]
        print(f"Using AWS profile: {aws_profile}")
    
    success = test_bedrock_access(aws_profile)
    
    if not success:
        show_bedrock_setup_help()
