"""Prompt management service for loading and formatting prompts."""
import json
import os
from pathlib import Path
from typing import Dict, Any

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def get_prompt(name: str) -> str:
    """Load a prompt template by name.
    
    Args:
        name: Prompt name (without extension)
        
    Returns:
        Prompt content as string
    """
    # Try .txt first
    txt_path = PROMPTS_DIR / f"{name}.txt"
    if txt_path.exists():
        return txt_path.read_text(encoding="utf-8")
    
    # Try .json
    json_path = PROMPTS_DIR / f"{name}.json"
    if json_path.exists():
        return json_path.read_text(encoding="utf-8")
    
    raise FileNotFoundError(f"Prompt not found: {name}")


def get_prompt_json(name: str) -> Dict[str, Any]:
    """Load a JSON prompt template.
    
    Args:
        name: Prompt name (without extension)
        
    Returns:
        Parsed JSON content
    """
    json_path = PROMPTS_DIR / f"{name}.json"
    if not json_path.exists():
        raise FileNotFoundError(f"JSON prompt not found: {name}")
    
    return json.load(json_path.open(encoding="utf-8"))


def format_prompt(template: str, **kwargs) -> str:
    """Format a prompt template with variables.
    
    Args:
        template: Template string with {placeholders}
        **kwargs: Variables to substitute
        
    Returns:
        Formatted prompt
    """
    return template.format(**kwargs)

