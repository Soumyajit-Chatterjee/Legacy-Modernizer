import click
import os
from backend.orchestrator import orchestrate_modernization

@click.command()
@click.option('--input-dir', '-i', required=True, help="Directory containing legacy Java code.")
@click.option('--output-dir', '-o', required=True, default="./modernized_output", help="Directory to save modernized code.")
@click.option('--target-lang', '-l', required=True, type=click.Choice(['python', 'go'], case_sensitive=False), help="Target language for modernization.")
@click.option('--target-function', '-f', required=True, help="The core function/method to modernize.")
def main(input_dir, output_dir, target_lang, target_function):
    """
    Legacy Code Modernization Engine Prototype
    Parses Java code, extracts dependencies, optimizes context by stripping comments, 
    and generates modern idiomatic code and tests.
    """
    if not os.environ.get("GEMINI_API_KEY"):
        click.echo("Warning: GEMINI_API_KEY environment variable is not set. The LLM step will fail.", err=True)
        
    print(f"Starting legacy code modernization process...")
    print(f"Input Dir: {input_dir}")
    print(f"Output Dir: {output_dir}")
    print(f"Target Language: {target_lang}")
    print(f"Target Function: {target_function}")
    print("-" * 40)
    
    orchestrate_modernization(input_dir, output_dir, target_lang, target_function)

if __name__ == '__main__':
    main()
