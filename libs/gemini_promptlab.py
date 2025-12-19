"""
PromptLab - Test and refine Gemini prompts with configs and validation. 
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import os

import google.generativeai as genai
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


def load_prompt_config(config_path: str) -> Dict[str, Any]:
    """
    Load a prompt configuration from a JSON file.
    
    Args:
        config_path: Path to the JSON config file
        
    Returns: 
        Dictionary with prompt configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config is invalid JSON
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r') as f:
        config = json.load(f)
    
    # Validate required fields
    required = ['name', 'model', 'user_prompt_template']
    missing = [field for field in required if field not in config]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
    
    logger.info(f"Loaded config:  {config['name']}")
    return config


def render_prompt(template: str, variables: Dict[str, Any]) -> str:
    """
    Render a prompt template with variables.
    
    Args:
        template: Prompt template with {variable} placeholders
        variables: Dictionary of variable values
        
    Returns:
        Rendered prompt string
    """
    try:
        return template.format(**variables)
    except KeyError as e:
        raise ValueError(f"Missing variable in template: {e}")


def validate_json_output(output: str, schema: Optional[Dict[str, Any]] = None) -> tuple[bool, Optional[Dict], Optional[str]]:
    """
    Validate JSON output against a schema.
    
    Args:
        output: String output from model
        schema: Optional JSON schema to validate against
        
    Returns:
        Tuple of (is_valid, parsed_json, error_message)
    """
    # Try to parse as JSON
    try: 
        parsed = json.loads(output)
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON: {str(e)}"
    
    # If schema provided, validate
    if schema:
        try: 
            validate(instance=parsed, schema=schema)
        except ValidationError as e: 
            return False, parsed, f"Schema validation failed: {e.message}"
    
    return True, parsed, None


def run_test_cases(
    config: Dict[str, Any],
    dry_run: bool = False,
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]: 
    """
    Run all test cases from a config. 
    
    Args:
        config:  Prompt configuration dictionary
        dry_run: If True, only render prompts without calling API
        api_key:  Gemini API key (uses GEMINI_API_KEY env var if not provided)
        
    Returns: 
        List of test results
    """
    results = []
    test_cases = config.get('test_cases', [])
    
    if not test_cases:
        logger.warning("No test cases found in config")
        return results
    
    # Configure Gemini if not dry run
    if not dry_run:
        key = api_key or os.getenv('GEMINI_API_KEY')
        if not key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        genai.configure(api_key=key)
        
        # Set up model
        gen_config = config.get('generation_config', {})
        model = genai.GenerativeModel(
            model_name=config['model'],
            system_instruction=config.get('system_instructions'),
            generation_config=gen_config
        )
    
    # Run each test case
    for idx, test_case in enumerate(test_cases, 1):
        logger.info(f"Running test case {idx}/{len(test_cases)}")
        
        result = {
            'test_case': idx,
            'input': test_case['input'],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Render prompt
            prompt = render_prompt(
                config['user_prompt_template'],
                test_case['input']
            )
            result['rendered_prompt'] = prompt
            
            if dry_run:
                result['status'] = 'dry_run'
                result['output'] = None
            else:
                # Call API
                response = model.generate_content(prompt)
                output = response.text
                result['output'] = output
                
                # Validate if schema provided
                schema = test_case.get('expected_json_schema')
                is_valid, parsed, error = validate_json_output(output, schema)
                
                result['valid'] = is_valid
                result['parsed_output'] = parsed
                result['validation_error'] = error
                result['status'] = 'pass' if is_valid else 'fail'
                
        except Exception as e:
            logger.error(f"Test case {idx} failed: {e}")
            result['status'] = 'error'
            result['error'] = str(e)
        
        results.append(result)
    
    return results


def write_report_md(
    config: Dict[str, Any],
    results: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Write test results to a Markdown report.
    
    Args:
        config: Prompt configuration
        results: List of test results
        output_path: Path to write report
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        # Header
        f.write(f"# PromptLab Report:  {config['name']}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Config summary
        f.write("## Configuration\n\n")
        f.write(f"- **Model:** {config['model']}\n")
        f.write(f"- **System Instructions:** {config.get('system_instructions', 'None')}\n")
        f.write(f"- **Temperature:** {config.get('generation_config', {}).get('temperature', 'default')}\n")
        f.write("\n")
        
        # Template
        f.write("## Prompt Template\n\n")
        f.write("```\n")
        f.write(config['user_prompt_template'])
        f.write("\n```\n\n")
        
        # Results summary
        passed = sum(1 for r in results if r.get('status') == 'pass')
        failed = sum(1 for r in results if r.get('status') == 'fail')
        errors = sum(1 for r in results if r.get('status') == 'error')
        dry_runs = sum(1 for r in results if r.get('status') == 'dry_run')
        
        f.write("## Summary\n\n")
        f.write(f"- **Total Tests:** {len(results)}\n")
        f.write(f"- **Passed:** {passed}\n")
        f.write(f"- **Failed:** {failed}\n")
        f.write(f"- **Errors:** {errors}\n")
        if dry_runs: 
            f.write(f"- **Dry Runs:** {dry_runs}\n")
        f.write("\n")
        
        # Individual results
        f.write("## Test Results\n\n")
        for result in results:
            f.write(f"### Test Case {result['test_case']}\n\n")
            f.write(f"**Status:** {result['status'].upper()}\n\n")
            
            # Input
            f.write("**Input:**\n```json\n")
            f.write(json.dumps(result['input'], indent=2))
            f.write("\n```\n\n")
            
            # Rendered prompt
            f.write("**Rendered Prompt:**\n```\n")
            f.write(result.get('rendered_prompt', ''))
            f.write("\n```\n\n")
            
            # Output
            if result.get('output'):
                f.write("**Output:**\n```\n")
                f.write(result['output'])
                f.write("\n```\n\n")
            
            # Validation
            if result.get('validation_error'):
                f.write(f"**Validation Error:** {result['validation_error']}\n\n")
            
            # Errors
            if result.get('error'):
                f.write(f"**Error:** {result['error']}\n\n")
            
            f.write("---\n\n")
    
    logger.info(f"Report written to:  {output_path}")