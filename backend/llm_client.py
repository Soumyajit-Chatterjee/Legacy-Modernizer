import os
from google import genai
from google.genai import types

def generate_modernized_code(context: dict, target_lang: str) -> dict:
    """
    Calls the Gemini API to modernize the context into target_lang and generate tests.
    Expects GEMINI_API_KEY to be set in the environment.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
        
    client = genai.Client()
    
    is_fallback = context.get("is_fallback", False)
    
    prompt = f"""
    You are an expert Legacy Code Modernization Engine.
    Your task is to translate an isolated piece of a legacy application into {target_lang}.
    """
    
    if is_fallback:
        prompt += f"""
        We extracted the raw COBOL bounded section relating to '{context['target_function']}'.
        Code Context:
        ```cobol
        {context['target_code_stripped']}
        ```
        """
    else:
        prompt += f"""
        Target Function to modernize: {context['target_function']}
        Code (comments stripped):
        ```java
        {context['target_code_stripped']}
        ```
        Here are the immediate dependencies of this function to give you necessary context:
        """
        for dep in context['dependencies']:
            prompt += f"""
            Dependency: {dep['name']}
            ```java
            {dep['code_stripped']}
            ```
            """
            
    prompt += f"""
    Based on the behavior of the legacy code, output the modernized equivalent in {target_lang}.
    Then, provide a suite of unit tests for the modernized code.
    
    Return exactly a JSON object with two fields:
    - "modernized_code": The modern {target_lang} equivalent code snippet using idiomatic patterns.
    - "unit_tests": The {target_lang} unit test code snippets.
    Do not use markdown code blocks inside the JSON values, just raw text.
    """
    
    # Note: the new google-genai SDK 
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2
        )
    )
    
    return response.text
