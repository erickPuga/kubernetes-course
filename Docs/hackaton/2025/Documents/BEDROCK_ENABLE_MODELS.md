# Fix: "Bedrock model not available" Error

## 🚨 You're getting this error because you need to enable model access in AWS Bedrock Console

The error means your AWS account can access Bedrock, but you haven't requested access to Claude models yet.

## Quick Fix Steps

### 1. Go to AWS Bedrock Console
```bash
# Open in your browser:
https://console.aws.amazon.com/bedrock/
```

### 2. Enable Model Access
1. **Click "Model access"** in the left sidebar
2. **Click "Request model access"** button
3. **Enable these Claude models:**
   - ✅ **Claude 3 Haiku** (fastest/cheapest for testing)
   - ✅ **Claude 3 Sonnet** (balanced, good default)
   - ✅ **Claude 3.5 Sonnet** (best quality)

### 3. Wait for Approval (Usually Instant)
- Most models are approved immediately
- Some might take a few minutes
- Status will show "Available" when ready

### 4. Test Again
```bash
# Test with fastest model first
export BEDROCK_MODEL_ID="anthropic.claude-3-haiku-20240307-v1:0"
python test_bedrock_access.py your-bedrock-profile
```

## Alternative: Use Available Models Only

### Check What Models You Already Have
```bash
python list_bedrock_models.py your-bedrock-profile
```

### Use Any Available Claude Model
If you see any Claude models listed, copy the exact model ID:
```bash
# Example - use whatever model ID you see
export BEDROCK_MODEL_ID="your-available-model-id-here"
python test_ai_conversion.py your-bedrock-profile
```

## Step-by-Step Bedrock Console Guide

### Navigate to Model Access
1. **Login to AWS Console** with your Bedrock profile
2. **Go to Services** → **Bedrock** (or search "bedrock")
3. **Ensure you're in us-west-2 region** (top right)
4. **Click "Model access"** in left sidebar

### Request Access to Claude Models
1. **Click "Request model access"** (orange button)
2. **Find "Anthropic" section**
3. **Check these boxes:**
   - ☐ Claude 3 Haiku
   - ☐ Claude 3 Sonnet  
   - ☐ Claude 3.5 Sonnet
4. **Click "Next"** and **"Submit"**

### Verify Access
After a few minutes:
1. **Refresh the page**
2. **Check Status column** shows "Available" 
3. **Test with our script:**
   ```bash
   python test_bedrock_access.py your-bedrock-profile
   ```

## If Models Still Not Available

### Check Region
Bedrock models might be in different regions:
```bash
# Try different regions
export AWS_DEFAULT_REGION=us-east-1
python test_bedrock_access.py your-bedrock-profile

export AWS_DEFAULT_REGION=us-west-2  
python test_bedrock_access.py your-bedrock-profile
```

### Contact Your AWS Admin
If you can't request model access:
- Contact your SkyTouch AWS administrator
- Ask them to enable Bedrock model access for your profile
- Mention you need "Claude models in Bedrock for AI development"

### Use Prompt Mode (Fallback)
If you can't get Bedrock working right now:
```bash
# This will create AI prompts you can use manually
python test_ai_conversion.py your-bedrock-profile

# It will save prompts to ./ai_prompts/ directory
# Copy those to Claude.ai or ChatGPT manually
```

## Expected Success Messages

When models are properly enabled, you should see:
```
✅ Bedrock service accessible  
✅ Found 3 Claude models:
    - anthropic.claude-3-haiku-20240307-v1:0
    - anthropic.claude-3-sonnet-20240229-v1:0  
    - anthropic.claude-3-5-sonnet-20241022-v2:0
✅ Bedrock Runtime works!
🤖 Test AI Response: Model test successful
```

## Quick Test Commands After Enabling

```bash
# 1. Verify models are available
python list_bedrock_models.py your-bedrock-profile

# 2. Test with fastest model
export BEDROCK_MODEL_ID="anthropic.claude-3-haiku-20240307-v1:0"
python test_bedrock_access.py your-bedrock-profile

# 3. Run full conversion test
python test_ai_conversion.py your-bedrock-profile
```

## SkyTouch-Specific Notes

Since you're at SkyTouch, you might need to:
1. **Use the correct AWS region** where your team has Bedrock enabled
2. **Contact IT/DevOps** if model access requests are restricted
3. **Use a different AWS profile** that has broader permissions

The good news is you have Bedrock access - you just need to enable the Claude models!
