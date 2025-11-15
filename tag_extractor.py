#!/usr/bin/env python3
"""
Tag Extractor - Extracts tags from user prompts using PydanticAI and OpenAI
"""

import sys
from pydantic_ai import Agent
from pydantic import BaseModel
from typing import List


class TagsResponse(BaseModel):
    """Response model containing extracted tags"""
    tags: List[str]


# Create the agent with OpenAI
agent = Agent(
    'openai:gpt-4o-mini',
    system_prompt='Extract relevant tags from the user prompt. Return a list of concise, meaningful tags that categorize or describe the main topics, themes, or keywords in the prompt.',
    result_type=TagsResponse,
)


def extract_tags(prompt: str) -> List[str]:
    """
    Extract tags from a user prompt.
    
    Args:
        prompt: The user's input prompt
        
    Returns:
        List of extracted tags
    """
    result = agent.run_sync(prompt)
    return result.data.tags


def main():
    """Main function to handle command line interaction"""
    if len(sys.argv) < 2:
        # If no arguments provided, read from stdin
        print("Enter your prompt (press Ctrl+D or Ctrl+Z to finish):", file=sys.stderr)
        try:
            prompt = sys.stdin.read().strip()
        except KeyboardInterrupt:
            print("\nCancelled.", file=sys.stderr)
            sys.exit(1)
    else:
        # Join all arguments as the prompt
        prompt = ' '.join(sys.argv[1:])
    
    if not prompt:
        print("Error: No prompt provided.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Processing prompt: {prompt}", file=sys.stderr)
    print("Extracting tags...", file=sys.stderr)
    
    try:
        tags = extract_tags(prompt)
        print("\nExtracted tags:")
        for tag in tags:
            print(f"  - {tag}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

