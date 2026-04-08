#!/usr/bin/env python3
"""
Test AI-Powered CloudFormation to Terraform Conversion
Demonstrates the AI conversion workflow
"""

import json
from pathlib import Path
from ai_converter import AIConverter
from colorama import Fore, Style, init

init()

def test_ai_conversion(aws_profile: str = None):
    """Test AI conversion with cached CloudFormation template"""
    
    print(f"{Fore.CYAN}🤖 Testing AI-Powered CF→TF Conversion{Style.RESET_ALL}")
    if aws_profile:
        print(f"🔧 Using AWS profile: {aws_profile}")
    print("=" * 60)
    
    # Find cached template
    cache_dir = Path('../cf_templates_cache')
    template_files = list(cache_dir.glob('*.json'))
    
    if not template_files:
        print(f"{Fore.RED}✗ No cached templates found{Style.RESET_ALL}")
        return
    
    # Use first template
    template_file = template_files[0]
    stack_name = template_file.stem
    
    print(f"📄 Using template: {template_file.name}")
    print(f"🏗️ Stack name: {stack_name}")
    
    # Load template
    with open(template_file, 'r') as f:
        template_data = json.load(f)
    
    # Handle string format from cache
    if isinstance(template_data, str):
        import yaml
        cf_template = yaml.safe_load(template_data)
    else:
        cf_template = template_data
    
    # Initialize AI converter (defaults to Bedrock)
    converter = AIConverter(ai_provider="bedrock", aws_profile=aws_profile)
    
    # Convert template
    result = converter.convert_template_with_ai(cf_template, stack_name)
    
    # Save results
    output_dir = f'./ai_output/{stack_name}'
    converter.save_conversion(result, output_dir)
    
    print(f"\n{Fore.GREEN}✅ AI conversion workflow complete!{Style.RESET_ALL}")
    print(f"📁 Output directory: {output_dir}")

if __name__ == '__main__':
    import sys
    
    # Check for profile argument
    aws_profile = None
    if len(sys.argv) > 1:
        aws_profile = sys.argv[1]
        print(f"Using AWS profile: {aws_profile}")
    
    test_ai_conversion(aws_profile)
