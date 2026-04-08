# Using CloudFormation to Terraform Converter with AWS Profiles

## Quick Start with AWS Profiles

If your Bedrock access is in a specific AWS profile (which is common), here's how to use the converter:

### 1. Test Bedrock Access with Your Profile

```bash
# Test with your Bedrock-enabled profile
python test_bedrock_access.py your-bedrock-profile-name

# Example:
python test_bedrock_access.py bedrock-dev
python test_bedrock_access.py skt-admin
python test_bedrock_access.py prod-access
```

### 2. Run CF→TF Conversion with Profile

```bash
# Convert templates using your profile
python test_ai_conversion.py your-bedrock-profile-name

# Example:
python test_ai_conversion.py bedrock-dev
```

### 3. Use in Python Code with Profile

```python
from ai_converter import AIConverter

# Initialize with your Bedrock profile
converter = AIConverter(aws_profile="bedrock-dev")

# Convert CloudFormation template
result = converter.convert_template_with_ai(cf_template, stack_name)

# Save results
converter.save_conversion(result, './terraform_output')
```

## AWS Profile Configuration

### Check Your Current Profiles
```bash
# List available AWS profiles
aws configure list-profiles

# Example output:
# default
# bedrock-dev  
# skt-admin
# prod-access
```

### Configure a New Profile (if needed)
```bash
# Configure a new profile for Bedrock access
aws configure --profile bedrock-dev

# Enter your credentials when prompted:
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY  
# Default region: us-west-2
# Default output format: json
```

### Test Profile Access
```bash
# Verify your profile works
aws sts get-caller-identity --profile bedrock-dev

# Should show your identity information
```

## Common Usage Patterns

### Pattern 1: Test First, Then Convert
```bash
# Step 1: Test Bedrock access
python test_bedrock_access.py bedrock-dev

# Step 2: If successful, run conversion
python test_ai_conversion.py bedrock-dev
```

### Pattern 2: Batch Processing with Profile
```python
#!/usr/bin/env python3
import json
from pathlib import Path
from ai_converter import AIConverter

def convert_all_templates(aws_profile):
    """Convert all cached CF templates using specific profile"""
    
    converter = AIConverter(aws_profile=aws_profile)
    cache_dir = Path('../cf_templates_cache')
    
    for template_file in cache_dir.glob('*.json'):
        print(f"Converting: {template_file.name}")
        
        with open(template_file, 'r') as f:
            cf_template = json.load(f)
        
        # Convert
        result = converter.convert_template_with_ai(cf_template, template_file.stem)
        
        # Save
        output_dir = f'./terraform_output/{template_file.stem}'
        converter.save_conversion(result, output_dir)

# Usage
convert_all_templates("bedrock-dev")
```

### Pattern 3: Environment Variables
```bash
# Set profile as environment variable
export AWS_PROFILE=bedrock-dev

# Then run without specifying profile
python test_bedrock_access.py
python test_ai_conversion.py
```

## Troubleshooting Profile Issues

### Profile Not Found
```bash
# Error: The config profile (bedrock-dev) could not be found
aws configure list-profiles  # Check available profiles
aws configure --profile bedrock-dev  # Create if missing
```

### Profile Has No Bedrock Access
```bash
# Test shows access denied
# Solution: Contact IT/DevOps to add Bedrock permissions to this profile
python test_bedrock_access.py bedrock-dev
```

### Wrong Region
```bash
# Bedrock might be in a different region
export AWS_DEFAULT_REGION=us-east-1
python test_bedrock_access.py bedrock-dev
```

## SkyTouch-Specific Tips

### Common SkyTouch Profile Names
Based on typical SkyTouch patterns, your Bedrock profile might be named:
- `bedrock-dev`
- `skt-admin`
- `dev-admin`
- `prod-access`
- `ml-access`

### Check with Your Team
Ask your team members:
- "What AWS profile do you use for Bedrock access?"
- "Which profile has AI/ML permissions?"
- "Is there a shared profile for development tools?"

### Request Profile Setup
If you don't have a Bedrock-enabled profile:
1. Contact IT/DevOps team
2. Request: "AWS profile with Bedrock permissions for Claude models"
3. Specify: "Need bedrock:InvokeModel and bedrock:ListFoundationModels"

## Example Commands Summary

```bash
# Test access
python test_bedrock_access.py your-profile-name

# Convert templates  
python test_ai_conversion.py your-profile-name

# Use in code
converter = AIConverter(aws_profile="your-profile-name")
```

Replace `your-profile-name` with your actual AWS profile that has Bedrock access!
