import os
import re
import json
import time
import random
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI, APIConnectionError, APITimeoutError, APIStatusError
from pydantic import ValidationError

from src.llm.schema import TriageResponse

load_dotenv()

PROMPT_FILE_PATH = os.path.join("prompts", "triage-v1.md")
QUARANTINE_LOG_PATH = os.path.join("logs", "quarantine.jsonl")
USAGE_LOG_PATH = os.path.join("logs", "usage.jsonl")


def load_system_prompt() -> str:
    if not os.path.exists(PROMPT_FILE_PATH):
        raise FileNotFoundError(f"Prompt file not found at: {PROMPT_FILE_PATH}")
    with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def clean_json_string(raw_text: str) -> str:
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def log_to_quarantine(user_input: str, error_msg: str, raw_output: str, prompt_version: str = "v1"):
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


def log_usage(model: str, prompt_tokens: int, completion_tokens: int, duration_ms: float, needed_repair: bool, prompt_version: str = "v1"):
    """Requirement 3: Log cost, latency, and token metrics per call."""
    os.makedirs("logs", exist_ok=True)
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_version": prompt_version,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "duration_ms": round(duration_ms, 2),
        "needed_repair": needed_repair,
    }
    with open(USAGE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")


def send_openrouter_request_with_retry(messages: list[dict]) -> tuple[str, dict]:
    """
    Requirements 1 & 2: 30s timeout, max_retries=0 on client, 
    custom exponential backoff with jitter on 429/5xx/timeout.
    """
    client = OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
        timeout=30.0,   # Requirement 1: 30 second timeout
        max_retries=0,  # Requirement 2: Explicitly disabled SDK defaults
    )

    max_attempts = 3
    base_delay = 1.0

    for attempt in range(1, max_attempts + 1):
        try:
            response = client.chat.completions.create(
                model=os.environ["LLM_MODEL"],
                temperature=0.0,
                messages=messages,
            )
            
            usage_stats = {
                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                "completion_tokens": getattr(response.usage, "completion_tokens", 0),
            }
            return response.choices[0].message.content, usage_stats

        except (APITimeoutError, APIConnectionError) as net_err:
            if attempt == max_attempts:
                raise TimeoutError("Request timed out after multiple retry attempts.") from net_err

        except APIStatusError as status_err:
            code = status_err.status_code
            # Requirement 2: NEVER retry 400, 401, 403
            if code in (400, 401, 403):
                raise status_err

            # Retry on 429 or 5xx
            if code == 429 or code >= 500:
                if attempt == max_attempts:
                    raise status_err
                
                # Check Retry-After header if present
                retry_after = status_err.response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    sleep_time = float(retry_after)
                else:
                    # Exponential backoff with jitter: 1s, 2s, 4s + random jitter
                    sleep_time = (base_delay * (2 ** (attempt - 1))) + random.uniform(0.1, 0.5)
                
                time.sleep(sleep_time)
                continue
            
            raise status_err


def parse_and_validate(raw_text: str) -> TriageResponse:
    cleaned_text = clean_json_string(raw_text)
    data_dict = json.loads(cleaned_text)
    return TriageResponse.model_validate(data_dict)


def call_llm_with_repair(user_input: str) -> TriageResponse:
    system_prompt = load_system_prompt()
    sanitized_user_content = json.dumps({"customer_message": user_input})
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": sanitized_user_content},
    ]

    start_time = time.time()
    total_prompt_tokens = 0
    total_completion_tokens = 0
    needed_repair = False

    try:
        raw_output_1, usage1 = send_openrouter_request_with_retry(messages)
        total_prompt_tokens += usage1["prompt_tokens"]
        total_completion_tokens += usage1["completion_tokens"]

        try:
            validated_result = parse_and_validate(raw_output_1)
            duration_ms = (time.time() - start_time) * 1000
            log_usage(
                model=os.environ["LLM_MODEL"],
                prompt_tokens=total_prompt_tokens,
                completion_tokens=total_completion_tokens,
                duration_ms=duration_ms,
                needed_repair=False,
            )
            return validated_result

        except (json.JSONDecodeError, ValidationError, Exception) as err1:
            needed_repair = True
            error_details_1 = str(err1)

            repair_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": sanitized_user_content},
                {"role": "assistant", "content": raw_output_1},
                {
                    "role": "user",
                    "content": (
                        f"Your previous answer was rejected for this reason:\n{error_details_1}\n\n"
                        f"Your previous broken output was:\n{raw_output_1}\n\n"
                        f"Return ONLY corrected raw JSON matching the required schema."
                    ),
                },
            ]

            raw_output_2, usage2 = send_openrouter_request_with_retry(repair_messages)
            total_prompt_tokens += usage2["prompt_tokens"]
            total_completion_tokens += usage2["completion_tokens"]

            validated_result_2 = parse_and_validate(raw_output_2)
            duration_ms = (time.time() - start_time) * 1000
            log_usage(
                model=os.environ["LLM_MODEL"],
                prompt_tokens=total_prompt_tokens,
                completion_tokens=total_completion_tokens,
                duration_ms=duration_ms,
                needed_repair=True,
            )
            return validated_result_2

    except APIStatusError:
        # Re-raise APIStatusError so src/routes/triage.py can return 401/403/400 instead of 422
        raise        

    except Exception as final_err:
        error_details = str(final_err)
        log_to_quarantine(
            user_input=user_input,
            error_msg=error_details,
            raw_output=locals().get("raw_output_2", locals().get("raw_output_1", "")),
            prompt_version="v1",
        )
        raise ValueError(error_details) from final_err