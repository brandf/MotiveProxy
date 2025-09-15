#!/usr/bin/env python3
"""
Environment Setup Script for MotiveProxy E2E Testing

This script helps you set up your .env file for LLM API keys.
"""

import os
import shutil
from pathlib import Path


def setup_env_file():
    """Set up .env file from template."""
    project_root = Path(__file__).parent
    template_file = project_root / 'env.template'
    env_file = project_root / '.env'
    
    if not template_file.exists():
        print("❌ Template file 'env.template' not found!")
        return False
    
    if env_file.exists():
        response = input("⚠️  .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("✅ Keeping existing .env file")
            return True
    
    try:
        shutil.copy2(template_file, env_file)
        print("✅ Created .env file from template")
        print(f"📝 Please edit {env_file} and add your API keys")
        print("\n🔑 You'll need at least one of these API keys:")
        print("   • GOOGLE_API_KEY (for Gemini models) - https://aistudio.google.com/app/apikey")
        print("   • OPENAI_API_KEY (for GPT models) - https://platform.openai.com/api-keys")
        print("   • ANTHROPIC_API_KEY (for Claude models) - https://console.anthropic.com/")
        print("   • COHERE_API_KEY (for Command models) - https://dashboard.cohere.ai/api-keys")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def check_env_file():
    """Check if .env file has API keys configured."""
    project_root = Path(__file__).parent
    env_file = project_root / '.env'
    
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    try:
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Check for placeholder values
        placeholders = [
            'your_openai_api_key_here',
            'your_anthropic_api_key_here', 
            'your_google_api_key_here',
            'your_cohere_api_key_here'
        ]
        
        has_real_keys = True
        for placeholder in placeholders:
            if placeholder in content:
                has_real_keys = False
                break
        
        if has_real_keys:
            print("✅ .env file appears to have real API keys configured")
            
            # Check which providers are configured
            providers = []
            if 'OPENAI_API_KEY=' in content and 'your_openai_api_key_here' not in content:
                providers.append('OpenAI')
            if 'ANTHROPIC_API_KEY=' in content and 'your_anthropic_api_key_here' not in content:
                providers.append('Anthropic')
            if 'GOOGLE_API_KEY=' in content and 'your_google_api_key_here' not in content:
                providers.append('Google')
            if 'COHERE_API_KEY=' in content and 'your_cohere_api_key_here' not in content:
                providers.append('Cohere')
            
            if providers:
                print(f"🎯 Configured providers: {', '.join(providers)}")
            else:
                print("⚠️  No API keys found in .env file")
            
            return len(providers) > 0
        else:
            print("⚠️  .env file still contains placeholder values")
            print("📝 Please edit .env file and replace placeholder values with real API keys")
            return False
            
    except Exception as e:
        print(f"❌ Failed to read .env file: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 MotiveProxy E2E Environment Setup")
    print("=" * 40)
    
    # Check if .env exists and is configured
    if check_env_file():
        print("\n✅ Environment is ready for E2E testing!")
        print("\n🧪 You can now run LLM tests:")
        print("   motive-proxy-e2e --scenario basic-handshake --use-llms")
        return
    
    # Offer to create .env file
    print("\n📋 Setting up environment file...")
    if setup_env_file():
        print("\n📝 Next steps:")
        print("1. Edit the .env file and add your API keys")
        print("2. Run this script again to verify configuration")
        print("3. Start E2E testing with LLMs!")


if __name__ == "__main__":
    main()
