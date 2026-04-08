#!/usr/bin/env python3
"""
Test script to verify CF to Terraform converter setup
"""

import sys
import subprocess
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import boto3
        import click
        import yaml
        import colorama
        print("  ✅ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        print("  💡 Run: pip install -r requirements.txt")
        return False

def test_aws_connection():
    """Test AWS connection without making actual calls"""
    print("🔌 Testing AWS setup...")
    
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ClientError
        
        # Try to create a client (doesn't make network calls yet)
        try:
            client = boto3.client('sts')  # Use STS for lightweight test
            # Try to get caller identity (minimal AWS call)
            response = client.get_caller_identity()
            print(f"  ✅ AWS credentials working - Account: {response.get('Account', 'Unknown')}")
            return True
        except NoCredentialsError:
            print("  ⚠️  AWS credentials not configured")
            print("  💡 Run: aws configure")
            return False
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidUserID.NotFound':
                print("  ⚠️  AWS credentials invalid")
            else:
                print(f"  ⚠️  AWS error: {e.response['Error']['Message']}")
            return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {str(e)}")
        return False

def test_script_syntax():
    """Test that the main script has valid syntax"""
    print("📝 Testing script syntax...")
    
    script_path = Path("cf-to-tf-converter.py")
    if not script_path.exists():
        print("  ❌ cf-to-tf-converter.py not found")
        return False
    
    try:
        # Test syntax by compiling (doesn't execute)
        with open(script_path, 'r') as f:
            source = f.read()
        compile(source, script_path, 'exec')
        print("  ✅ Script syntax is valid")
        return True
    except SyntaxError as e:
        print(f"  ❌ Syntax error: {e}")
        return False

def test_help_command():
    """Test that the script's help command works"""
    print("📖 Testing help command...")
    
    try:
        result = subprocess.run(
            [sys.executable, "cf-to-tf-converter.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and "CloudFormation to Terraform Converter" in result.stdout:
            print("  ✅ Help command works")
            return True
        else:
            print(f"  ❌ Help command failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("  ❌ Help command timed out")
        return False
    except Exception as e:
        print(f"  ❌ Error running help: {str(e)}")
        return False

def main():
    """Run all setup tests"""
    print("🚀 CF to Terraform Converter - Setup Test")
    print("=" * 50)
    
    tests = [
        ("Module imports", test_imports),
        ("AWS connection", test_aws_connection),
        ("Script syntax", test_script_syntax),
        ("Help command", test_help_command)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"  ❌ Test '{test_name}' crashed: {str(e)}")
            results[test_name] = False
        print()
    
    # Summary
    print("📊 Test Summary:")
    print("-" * 30)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Ready for Phase 1 testing.")
        print("\n💡 Next steps:")
        print("  1. Try: python cf-to-tf-converter.py --pattern '*' --list-only")
        print("  2. Test with a real stack: python cf-to-tf-converter.py --stack-name <your-stack>")
    else:
        print("\n⚠️  Some tests failed. Please fix issues before proceeding.")
        
        if not results.get("Module imports", True):
            print("  🔧 Install dependencies: pip install -r requirements.txt")
        
        if not results.get("AWS connection", True):
            print("  🔧 Configure AWS: aws configure")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
