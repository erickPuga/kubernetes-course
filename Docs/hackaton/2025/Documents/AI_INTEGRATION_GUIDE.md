# How to Connect the Python Code with AI (Claude/Cline)

## Overview
The `ai_converter.py` supports multiple ways to integrate with AI services for CloudFormation to Terraform conversion.

## Method 1: Manual Integration with Cline (RECOMMENDED)

This is the easiest way to use the converter with Cline right now:

### Steps:
1. **Run the converter in prompt mode:**
```bash
python test_ai_conversion.py
```

2. **The script will:**
   - Generate a comprehensive AI prompt in `./ai_prompts/cf_to_tf_prompt_YYYYMMDD_HHMMSS.txt`
   - Include your CloudFormation template + SkyTouch context
   - Show you exactly what to copy

3. **Copy the prompt to Cline:**
   - Open the generated prompt file
   - Copy the entire content
   - Paste it into Cline (this conversation!)
   - Cline will generate the Terraform files

4. **Process Cline's response:**
```python
from ai_converter import AIConverter

# Save Cline's response to a file
converter = AIConverter()
result = converter.parse_manual_ai_response('cline_response.txt', 'your-stack-name')
converter.save_conversion(result, './terraform_output')
```

## Method 2: Claude API Integration (AUTOMATIC)

For direct API integration:

### Setup:
1. **Get Claude API key:**
   - Sign up at https://console.anthropic.com/
   - Create an API key

2. **Set environment variable:**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

3. **Install required library:**
```bash
pip install anthropic
```

4. **Use Claude API mode:**
```python
from ai_converter import AIConverter

# Initialize with Claude API
converter = AIConverter(ai_provider="claude")

# Convert template automatically
result = converter.convert_template_with_ai(cf_template, stack_name)
```

## Method 3: OpenAI Integration

Similar to Claude but with OpenAI:

```bash
export OPENAI_API_KEY="your-openai-key"
pip install openai
```

```python
converter = AIConverter(ai_provider="openai")
result = converter.convert_template_with_ai(cf_template, stack_name)
```

## Method 4: Local AI Integration

For privacy/offline use:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama2
```

```python
converter = AIConverter(ai_provider="local")
result = converter.convert_template_with_ai(cf_template, stack_name)
```

## Complete Workflow Example

Here's how to use it with your CloudFormation templates:

### Step 1: Generate AI Prompt
```python
#!/usr/bin/env python3
import json
import yaml
from ai_converter import AIConverter

# Load your CloudFormation template
with open('../cf_templates_cache/INT03-HOS-ISO-EC2.json', 'r') as f:
    template_data = json.load(f)

# Parse if stored as string
if isinstance(template_data, str):
    cf_template = yaml.safe_load(template_data)
else:
    cf_template = template_data

# Create converter in prompt mode
converter = AIConverter(ai_provider="prompt")

# Generate prompt for manual AI processing
result = converter.convert_template_with_ai(cf_template, "INT03-HOS-ISO-EC2")

print("Prompt generated! Check ./ai_prompts/ directory")
```

### Step 2: Use with Cline
1. Run the script above
2. Copy the generated prompt from `./ai_prompts/cf_to_tf_prompt_*.txt`
3. Paste it to Cline and ask: "Please process this CloudFormation to Terraform conversion"

### Step 3: Process Cline's Response
```python
# Save Cline's response to a text file, then:
converter = AIConverter()
result = converter.parse_manual_ai_response('cline_response.txt', 'INT03-HOS-ISO-EC2')
output_path = converter.save_conversion(result, './terraform_output/INT03-HOS-ISO-EC2')

print(f"Terraform files saved to: {output_path}")
```

## What the AI Prompt Contains

The generated prompt includes:
- **SkyTouch Context**: Company patterns, tagging standards, naming conventions
- **Stack Metadata**: Extracted app_name, environment, resource types
- **Full CloudFormation Template**: Your actual CF template in clean YAML
- **Detailed Requirements**: Specific instructions for Terraform generation
- **Output Format**: Structured format for easy parsing

## Sample Prompt Structure

```
Convert this CloudFormation template to Terraform with SkyTouch best practices:

SkyTouch Technology Context:
- Company transitioning from CloudFormation to Terraform
- Standard tagging: app_name, app_environment_id, environment, automation, etc.
- Environment patterns: INT (int03), PROD (prod01)
[... more context ...]

STACK INFORMATION:
- Stack Name: INT03-HOS-ISO-EC2
- App Name: hos-iso
- Environment: INT
- Resource Types: AWS::EC2::LaunchTemplate, AWS::AutoScaling::AutoScalingGroup

CLOUDFORMATION TEMPLATE:
```yaml
[Your actual CloudFormation template here]
```

REQUIREMENTS:
1. Generate complete, working Terraform configuration
2. Create separate files: main.tf, variables.tf, outputs.tf, provider.tf
[... detailed requirements ...]
```

## Benefits of Each Method

### Manual (Cline) Integration:
- ✅ Full control over AI interaction
- ✅ Can review and modify prompts
- ✅ Works with any AI service
- ✅ No API costs
- ❌ Manual copy/paste required

### API Integration:
- ✅ Fully automated
- ✅ Batch processing possible
- ✅ Programmable workflows
- ❌ Requires API keys and costs
- ❌ Less control over interaction

## Recommended Workflow for SkyTouch

1. **Start with Manual/Cline approach** for initial testing
2. **Use API integration** for production automation
3. **Combine both**: Manual for complex stacks, API for simple ones

This gives you the best of both worlds: control when you need it, automation when you want it.
