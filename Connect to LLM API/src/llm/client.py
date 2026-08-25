import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

PROMPT_FILE_PATH = os.path.join("prompts", "triage-v1.md")


def load_system_prompt() -> str:
    """Reads and returns the system prompt file from disk."""
    if not os.path.exists(PROMPT_FILE_PATH):
        raise FileNotFoundError(f"Prompt file not found at: {PROMPT_FILE_PATH}")

    with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def call_llm(user_input: str) -> str:
    """
    Sends the system prompt and untrusted user input to OpenRouter.
    Applies temperature=0.0 for deterministic classification responses.
    """
    system_prompt = load_system_prompt()

    # Create OpenAI client pointing to OpenRouter
    client = OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
    )

    # Keep user input isolated inside the user role and JSON-encoded to defend against prompt injection
    sanitized_user_content = json.dumps({"customer_message": user_input})

    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        temperature=0.0,  # Low temperature for deterministic output
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": sanitized_user_content},
        ],
    )

    # Return raw text response content from the model
    return response.choices[0].message.content