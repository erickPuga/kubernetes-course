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
    converter = AIConverter(aws_profile="int")
    
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
