#!/usr/bin/env python3
"""
Script to synchronize infrastructure templates with current environment configuration.
This updates the Bicep templates to match your existing Azure resources.
"""

import os
import re
from pathlib import Path


def read_env_file():
    """Read the .env file and extract Azure configuration."""
    # Look for .env in parent directory since we're in infra/
    env_file = Path("../.env")
    if not env_file.exists():
        print("❌ .env file not found in parent directory!")
        return None

    config = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key] = value.strip('"')

    return config


def extract_resource_info(config):
    """Extract resource names and deployments from environment config."""
    info = {}

    # Extract AI Service name from endpoint
    ai_endpoint = config.get('AZURE_AI_SERVICE_ENDPOINT', '')
    if ai_endpoint:
        match = re.search(
            r'https://([^.]+)\.services\.ai\.azure\.com', ai_endpoint)
        if match:
            info['ai_service_name'] = match.group(1)

    # Extract OpenAI resource name from endpoint
    openai_endpoint = config.get('AZURE_OPENAI_ENDPOINT', '')
    if openai_endpoint:
        match = re.search(
            r'https://([^.]+)\.openai\.azure\.com', openai_endpoint)
        if match:
            info['openai_name'] = match.group(1)

    # Extract Search service name from endpoint
    search_endpoint = config.get('AZURE_SEARCH_ENDPOINT', '')
    if search_endpoint:
        match = re.search(
            r'https://([^.]+)\.search\.windows\.net', search_endpoint)
        if match:
            info['search_name'] = match.group(1)

    # Get deployment names
    info['gpt_deployment'] = config.get(
        'AZURE_OPENAI_CHAT_DEPLOYMENT_NAME', 'gpt-5-mini')
    info['embedding_deployment'] = config.get(
        'AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME', 'text-embedding-3-small')

    return info


def update_bicep_template(resource_info):
    """Update the main.bicep template with current resource information."""
    bicep_file = Path("main.bicep")  # Now we're in infra/ directory
    if not bicep_file.exists():
        print("❌ main.bicep not found!")
        return

    with open(bicep_file, 'r') as f:
        content = f.read()

    print("🔧 Updating Bicep template with your environment configuration...")

    # Update model deployment names if we have the info
    if 'gpt_deployment' in resource_info:
        # Update default GPT model name
        content = re.sub(
            r"param gptModelName string = '[^']*'",
            f"param gptModelName string = '{resource_info['gpt_deployment']}'",
            content
        )
        # Update default GPT deployment name
        content = re.sub(
            r"param gptDeploymentName string = '[^']*'",
            f"param gptDeploymentName string = '{resource_info['gpt_deployment']}'",
            content
        )

    if 'embedding_deployment' in resource_info:
        # Update default embedding model name
        content = re.sub(
            r"param embeddingModelName string = '[^']*'",
            f"param embeddingModelName string = '{resource_info['embedding_deployment']}'",
            content
        )
        # Update default embedding deployment name
        content = re.sub(
            r"param embeddingDeploymentName string = '[^']*'",
            f"param embeddingDeploymentName string = '{resource_info['embedding_deployment']}'",
            content
        )

    # Write updated content
    with open(bicep_file, 'w') as f:
        f.write(content)

    print("✅ Updated main.bicep with your configuration")


def create_env_specific_parameters(resource_info):
    """Create a parameters file that matches your current environment."""
    params_content = f'''{{
    "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
    "contentVersion": "1.0.0.0",
    "parameters": {{
        "environmentName": {{
            "value": "wordonawing"
        }},
        "location": {{
            "value": "westus"
        }},
        "gptModelName": {{
            "value": "{resource_info.get('gpt_deployment', 'gpt-5-mini')}"
        }},
        "gptDeploymentName": {{
            "value": "{resource_info.get('gpt_deployment', 'gpt-5-mini')}"
        }},
        "embeddingModelName": {{
            "value": "{resource_info.get('embedding_deployment', 'text-embedding-3-small')}"
        }},
        "embeddingDeploymentName": {{
            "value": "{resource_info.get('embedding_deployment', 'text-embedding-3-small')}"
        }},
        "principalId": {{
            "value": "${{AZURE_PRINCIPAL_ID}}"
        }},
        "runningOnGitHub": {{
            "value": "${{GITHUB_ACTIONS}}"
        }}
    }}
}}'''

    with open("main.parameters.local.json", 'w') as f:
        f.write(params_content)

    print("✅ Created main.parameters.local.json for your environment")


def main():
    print("🔄 Synchronizing infrastructure templates with your environment...")

    # Read current environment
    config = read_env_file()
    if not config:
        return

    # Extract resource information
    resource_info = extract_resource_info(config)

    print(f"📊 Detected configuration:")
    print(
        f"   • AI Service: {resource_info.get('ai_service_name', 'Not detected')}")
    print(
        f"   • OpenAI Service: {resource_info.get('openai_name', 'Not detected')}")
    print(
        f"   • Search Service: {resource_info.get('search_name', 'Not detected')}")
    print(
        f"   • GPT Deployment: {resource_info.get('gpt_deployment', 'Not detected')}")
    print(
        f"   • Embedding Deployment: {resource_info.get('embedding_deployment', 'Not detected')}")

    # Update templates
    update_bicep_template(resource_info)
    create_env_specific_parameters(resource_info)

    print("🎯 Infrastructure templates now match your environment!")
    print("💡 You can now use 'azd up' to replicate this setup in other environments.")


if __name__ == "__main__":
    main()
