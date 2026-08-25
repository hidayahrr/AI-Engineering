import os
import re
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError

from src.llm.schema import TriageResponse

# Load environment variables
load_dotenv()

PROMPT_FILE_PATH = os.path.join("prompts", "triage-v1.md")
QUARANTINE_LOG_PATH = os.path.join("logs", "quarantine.jsonl")


def load_system_prompt() -> str:
    """Reads and returns the system prompt file from disk."""
    if not os.path.exists(PROMPT_FILE_PATH):
        raise FileNotFoundError(f"Prompt file not found at: {PROMPT_FILE_PATH}")

    with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def clean_json_string(raw_text: str) -> str:
    """
    Strips Markdown code blocks (```json ... ```) and leading/trailing whitespace
    to isolate the raw JSON object string.
    """
    text = raw_text.strip()
    # Remove ```json ... ``` or ``` ... ``` wrappers if present
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def log_to_quarantine(user_input: str, error_msg: str, raw_output: str, prompt_version: str = "v1"):
    """
    Logs failed responses to logs/quarantine.jsonl in line-delimited JSON format.
    Never crashes the application.
    """
    os.makedirs("logs", exist_ok=True)
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_version": prompt_version,
        "input": user_input,
        "error": error_msg,
        "raw_model_output": raw_output,
    }

    with open(QUARANTINE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")


def send_openrouter_request(messages: list[dict]) -> str:
    """Internal helper to execute OpenAI API completion call."""
    client = OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
    )

    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        temperature=0.0,  # Low temperature for deterministic outputs
        messages=messages,
    )

    return response.choices[0].message.content


def parse_and_validate(raw_text: str) -> TriageResponse:
    """
    Cleans raw LLM output, converts to dict via json.loads,
    and validates using Pydantic TriageResponse model.
    """
    cleaned_text = clean_json_string(raw_text)
    data_dict = json.loads(cleaned_text)
    return TriageResponse.model_validate(data_dict)


def call_llm_with_repair(user_input: str) -> TriageResponse:
    """
    Main LLM invocation logic for Stage 3:
    1. Loads prompt and sends request.
    2. Cleans, parses, and validates JSON.
    3. If validation fails, executes EXACTLY ONE repair retry.
    4. If repair fails, logs to logs/quarantine.jsonl and raises ValueError.
    """
    system_prompt = load_system_prompt()
    sanitized_user_content = json.dumps({"customer_message": user_input})

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": sanitized_user_content},
    ]

    # --- Attempt 1: First Model Call ---
    raw_output_1 = send_openrouter_request(messages)

    try:
        # Try to parse and validate Attempt 1
        validated_result = parse_and_validate(raw_output_1)
        return validated_result

    except (json.JSONDecodeError, ValidationError, Exception) as err1:
        error_details_1 = str(err1)

        # --- Attempt 2: Repair Retry (Exactly One Retry) ---
        repair_user_message = (
            f"Your previous answer was rejected for this reason:\n{error_details_1}\n\n"
            f"Your previous broken output was:\n{raw_output_1}\n\n"
            f"Return ONLY corrected raw JSON matching the required schema. Do not add any text."
        )

        repair_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": sanitized_user_content},
            {"role": "assistant", "content": raw_output_1},
            {"role": "user", "content": repair_user_message},
        ]

        try:
            raw_output_2 = send_openrouter_request(repair_messages)
            validated_result_2 = parse_and_validate(raw_output_2)
            return validated_result_2

        except (json.JSONDecodeError, ValidationError, Exception) as err2:
            error_details_2 = f"Initial Error: {error_details_1} | Repair Error: {str(err2)}"
            
            # Log failure to quarantine file
            log_to_quarantine(
                user_input=user_input,
                error_msg=error_details_2,
                raw_output=raw_output_2 if 'raw_output_2' in locals() else raw_output_1,
                prompt_version="v1"
            )

            # Raise ValueError so FastAPI endpoint can return HTTP 422
            raise ValueError(f"Output failed schema validation after 1 repair attempt: {error_details_2}")