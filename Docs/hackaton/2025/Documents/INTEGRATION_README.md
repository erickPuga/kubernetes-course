# Integrated CloudFormation to Terraform Converter

This document describes the integrated converter that combines template fetching and AI-powered conversion into a single streamlined workflow.

## Overview

The `cf_to_tf_converter.py` orchestrates two main components:

1. **CFTemplateReader** (from `get_stack_templates.py`) - Fetches CloudFormation templates from AWS
2. **AIConverter** (from `ai_converter.py`) - Converts templates to Terraform using AWS Bedrock AI

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  IntegratedConverter                         │
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │ CFTemplateReader │────────▶│   AIConverter    │          │
│  │                  │         │                  │          │
│  │ • AWS Connect    │         │ • Bedrock AI     │          │
│  │ • Discover Stacks│         │ • Prompt Build   │          │
│  │ • Fetch Templates│         │ • TF Generation  │          │
│  │ • Validate       │         │ • File Saving    │          │
│  └──────────────────┘         └──────────────────┘          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
            ┌──────────────────────────┐
            │  integrated_output/      │
            │    └── stack-name/       │
            │        ├── main.tf       │
            │        ├── variables.tf  │
            │        ├── outputs.tf    │
            │        └── ...           │
            └──────────────────────────┘
```

## Features

### End-to-End Workflow
- ✅ Automatic AWS authentication with profile support
- ✅ Stack discovery with pattern matching
- ✅ Template caching for faster re-runs
- ✅ AI-powered conversion to Terraform
- ✅ Organized output structure per stack
- ✅ Comprehensive error handling
- ✅ Detailed conversion reports

### Flexible Options
- Single stack or multiple stacks
- Pattern matching (wildcards)
- Fetch-only mode (skip conversion)
- Cache control
- AWS profile support
- Region selection

## Usage

### Basic Examples

#### Convert a single stack
```bash
cd cf-to-tf-converter
python integrated_converter.py --stack-name my-web-app
```

#### Convert multiple stacks
```bash
python integrated_converter.py --stack-names "app1,app2,app3"
```

#### Convert all stacks matching a pattern
```bash
python integrated_converter.py --pattern "web-*" --region us-west-2
```

#### Use a specific AWS profile
```bash
python integrated_converter.py --stack-name my-app --profile skytouch-prod
```

#### Only fetch templates (skip AI conversion)
```bash
python integrated_converter.py --stack-name my-app --fetch-only
```

### Advanced Options

```bash
python integrated_converter.py \
  --stack-name INT03-HOS-ISO-EC2 \
  --region us-west-2 \
  --profile skytouch-int \
  --ai-provider bedrock
```

### Command-Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--stack-name` | `-s` | Single CloudFormation stack name |
| `--stack-names` | `-n` | Comma-separated list of stack names |
| `--pattern` | `-p` | Wildcard pattern to match stack names |
| `--region` | `-r` | AWS region (default: us-west-2) |
| `--profile` | | AWS profile for both CF and Bedrock |
| `--ai-provider` | | AI provider: bedrock (default), prompt |
| `--no-cache` | | Disable template caching |
| `--fetch-only` | | Only fetch templates, skip conversion |

## Workflow Steps

The integrated converter executes in these steps:

### Step 1: Connect to AWS
- Establishes connection to AWS CloudFormation
- Uses specified profile or default credentials
- Validates access permissions

### Step 2: Discover Stacks
- Lists CloudFormation stacks matching criteria
- Supports exact names or wildcard patterns
- Displays discovered stacks with status

### Step 3: Fetch and Convert
For each stack:
1. **Fetch Template** - Retrieves CloudFormation template from AWS
2. **Validate** - Analyzes template structure and complexity
3. **Convert** - Sends to AI for Terraform conversion
4. **Save** - Organizes output files by stack name

### Step 4: Summary
- Displays conversion statistics
- Lists output directories
- Reports any failures
- Provides next steps

## Output Structure

```
integrated_output/
└── stack-name/
    ├── main.tf                    # Main Terraform resources
    ├── variables.tf               # Variable definitions
    ├── outputs.tf                 # Output values
    ├── provider.tf                # Provider configuration
    ├── terraform.tfvars.example   # Example variable values
    ├── conversion_notes.md        # AI conversion notes
    ├── ai_conversion_report.json  # Detailed conversion metadata
    ├── ai_prompt.txt              # Original AI prompt used
    └── ai_response_raw.txt        # Raw AI response
```

## Integration Benefits

### Compared to Separate Scripts

**Before (2 separate steps):**
```bash
# Step 1: Fetch template
python get_stack_templates.py --stack-name my-app

# Step 2: Convert with AI
python manual_test_ai_converter.py
```

**After (1 integrated step):**
```bash
python integrated_converter.py --stack-name my-app
```

### Advantages

1. **Simplified Workflow** - One command does everything
2. **Consistent Parameters** - Single AWS profile used throughout
3. **Better Error Handling** - Integrated error reporting
4. **Progress Tracking** - Clear step-by-step feedback
5. **Organized Output** - All artifacts in one location
6. **Cache Optimization** - Smart caching across workflow

## AWS Profile Support

The integrated converter uses a single AWS profile for both:
- CloudFormation template fetching
- Bedrock AI API calls

### Setup Profile

```bash
# Configure AWS profile
aws configure --profile skytouch-int

# Use in converter
python integrated_converter.py \
  --stack-name my-app \
  --profile skytouch-int
```

### Profile Requirements

The AWS profile needs:
- CloudFormation read permissions
- Bedrock model access (if using AI conversion)

See `AWS_BEDROCK_SETUP.md` for detailed permission setup.

## Error Handling

The integrated converter handles errors gracefully:

- **AWS Connection Failures** - Clear error messages with guidance
- **Stack Not Found** - Continues with other stacks
- **Template Fetch Errors** - Logged and reported
- **AI Conversion Failures** - Saves prompt file for manual processing
- **Partial Success** - Reports what succeeded and what failed

## Best Practices

### 1. Start with Fetch-Only
First run with `--fetch-only` to verify stack access:
```bash
python integrated_converter.py --stack-name my-app --fetch-only
```

### 2. Use Caching
Cache speeds up iterative testing:
```bash
# First run - fetches from AWS
python integrated_converter.py --stack-name my-app

# Subsequent runs - uses cache
python integrated_converter.py --stack-name my-app
```

### 3. Test with One Stack
Before batch conversion, test with a single stack:
```bash
python integrated_converter.py --stack-name simple-stack
```

### 4. Review AI Output
Always review generated Terraform:
- Check `conversion_notes.md` for manual steps
- Run `terraform plan` to validate
- Test in non-production first

## Troubleshooting

### "AWS credentials not found"
```bash
# Configure AWS CLI
aws configure --profile your-profile

# Use profile with converter
python integrated_converter.py --profile your-profile --stack-name my-app
```

### "Access denied for Bedrock"
- Check Bedrock permissions in IAM
- See `AWS_BEDROCK_SETUP.md` for setup
- Verify model access in AWS Console

### "No stacks found"
- Verify stack name/pattern is correct
- Check region setting
- Ensure AWS credentials have CloudFormation access

### "Conversion failed"
- Check `ai_prompts/` directory for saved prompt
- Manually process with Claude/ChatGPT
- Review error messages for specific issues

## Next Steps After Conversion

1. **Review Generated Files**
   ```bash
   cd integrated_output/your-stack-name
   ls -la
   ```

2. **Check Conversion Notes**
   ```bash
   cat conversion_notes.md
   ```

3. **Initialize Terraform**
   ```bash
   terraform init
   ```

4. **Validate Configuration**
   ```bash
   terraform validate
   terraform plan
   ```

5. **Apply (when ready)**
   ```bash
   terraform apply
   ```

## Related Documentation

- `README.md` - Main project documentation
- `AI_INTEGRATION_GUIDE.md` - AI integration details
- `AWS_BEDROCK_SETUP.md` - Bedrock permission setup
- `PROFILE_USAGE.md` - AWS profile configuration
- `TESTING_GUIDE.md` - Testing procedures

## Support

For issues or questions:
1. Check error messages and troubleshooting section
2. Review related documentation
3. Verify AWS permissions and Bedrock access
4. Check `ai_conversion_report.json` for details
