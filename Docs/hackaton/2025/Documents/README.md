# CF to Terraform Converter - Hackathon Project

## Phase 1: CloudFormation Template Reading

This is the first phase of our hackathon project to convert CloudFormation stacks to Terraform using AI assistance.

## Setup

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure AWS Credentials

Make sure you have AWS credentials configured. You can use any of these methods:

```bash
# Option 1: AWS CLI configuration
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1

# Option 3: AWS Profile
aws configure --profile your-profile-name
```

### 3. Required AWS Permissions

Your AWS credentials need these permissions:
- `cloudformation:ListStacks`
- `cloudformation:DescribeStacks`  
- `cloudformation:GetTemplate`

## Usage

### Basic Examples

```bash
# Read a single stack
python cf-to-tf-converter.py --stack-name my-web-app

# Read multiple stacks
python cf-to-tf-converter.py --stack-names "app1,app2,app3"

# Use wildcard pattern
python cf-to-tf-converter.py --pattern "web-*"

# Specify region and profile
python cf-to-tf-converter.py --stack-name my-app --region us-west-2 --profile my-profile

# List stacks only (don't download templates)
python cf-to-tf-converter.py --pattern "*" --list-only

# Disable caching
python cf-to-tf-converter.py --stack-name my-app --no-cache
```

### Command Line Options

- `--stack-name, -s`: Single CloudFormation stack name
- `--stack-names, -n`: Comma-separated list of stack names  
- `--pattern, -p`: Wildcard pattern to match stack names
- `--region, -r`: AWS region (default: us-east-1)
- `--profile`: AWS profile to use
- `--no-cache`: Disable template caching
- `--list-only`: Only list stacks, don't retrieve templates

## Output

The script creates:
- `cf_templates_cache/`: Directory containing cached templates and analysis
- `{stack-name}.json`: Cached CloudFormation template
- `{stack-name}_analysis.json`: Template analysis and metadata

## Phase 1 Features

✅ **AWS Integration**: Connect to CloudFormation API with proper authentication  
✅ **Stack Discovery**: Find stacks by name or wildcard patterns  
✅ **Template Retrieval**: Download and cache CF templates  
✅ **Template Analysis**: Parse and analyze template structure  
✅ **Error Handling**: Comprehensive error handling and user feedback  
✅ **Caching**: Local caching to avoid repeated API calls  
✅ **CLI Interface**: User-friendly command-line interface  

## Next Steps (Phase 2)

- [ ] AI integration for CF to Terraform conversion
- [ ] Docker container for Terraform validation
- [ ] SkyTouch pattern integration
- [ ] Enhanced resource mapping

## Troubleshooting

### Common Issues

**"AWS credentials not found"**
- Configure AWS credentials using `aws configure` or environment variables

**"Stack not found"**
- Verify the stack name exists in the specified region
- Check if you have permissions to access the stack

**"Access denied"** 
- Ensure your AWS credentials have CloudFormation read permissions
- Check if the stack is in a different account

**Import errors**
- Make sure you've installed all dependencies: `pip install -r requirements.txt`
- Activate your virtual environment if using one

## Development

To contribute or modify the script:

1. Follow PEP 8 style guidelines
2. Add type hints for new functions
3. Update tests for new functionality
4. Maintain backward compatibility

## License

This project is for the SkyTouch Hackathon 2025.
