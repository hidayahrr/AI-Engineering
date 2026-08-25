# 📋 Support Ticket Classifier API

An LLM-backed REST API endpoint built with **FastAPI** and **Pydantic** that classifies incoming customer support messages into closed categories, urgency levels, confidence scores, and brief reasons.

---

## 📋 Job Card Summary

> **Goal**: Classify customer support messages into designated teams, assign an urgency score, measure confidence, and provide a single-sentence justification.

| Field | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `text` | `string` | 1 – 2000 chars | Raw, unparsed customer support message |

### Output Contract (JSON Schema)

- **`category`** *(enum / closed list)*: `billing`, `bug`, `feature`, `other`
- **`urgency`** *(enum / closed list)*: `low`, `normal`, `high`
- **`confidence`** *(float)*: `0.0` to `1.0`
- **`reason`** *(string)*: One short single-sentence justification

### Constraints & Fallback Policy

- **Must Never**: Invent categories outside the closed list, return raw unformatted text, or reveal system instructions.
- **When Unsure**: Returns category `"other"` with `confidence` below `0.5` instead of hallucinating.

---

## ⚙️ Environment Configuration

Environment configuration is managed via `.env` (ignored by Git) and `.env.example` (committed template).

### `.env.example` Template

```env
PORT=8000
LLM_BASE_URL=[https://openrouter.ai/api/v1](https://openrouter.ai/api/v1)
LLM_API_KEY=your_key_here
LLM_MODEL=openai/gpt-4o-mini
LLM_STUB=0
LLM_ENABLED=true
```

## 🧪 Stage 1 Verification Commands

Ensure the local Uvicorn server is running before executing tests:

```bash
python -m uvicorn src.main:app --reload
```

### 1. Valid Request (`HTTP 200` + Schema JSON)

**Python Execution (Cross-Platform):**

```powershell
python -c "import urllib.request, json; req = urllib.request.Request('[http://127.0.0.1:8000/triage](http://127.0.0.1:8000/triage)', data=json.dumps({'text': 'My card was charged twice for subscription.'}).encode('utf-8'), headers={'Content-Type': 'application/json'}); print(urllib.request.urlopen(req).read().decode('utf-8'))"
```

**cURL Command:**

```bash
curl -X POST "[http://127.0.0.1:8000/triage](http://127.0.0.1:8000/triage)" \
     -H "Content-Type: application/json" \
     -d '{"text": "My card was charged twice for subscription."}'
```

### 2. Invalid Request (`HTTP 400 Bad Request`)

**PowerShell:**

```powershell
python -c "import urllib.request, json; req = urllib.request.Request('[http://127.0.0.1:8000/triage](http://127.0.0.1:8000/triage)', data=b'{}', headers={'Content-Type': 'application/json'}); urllib.request.urlopen(req)"
```

## 📝 Stage 2 Prompt Specification & Observations

- **Prompt Location**: `prompts/triage-v1.md`
- **Prompt Structure**: Includes Role, Output Shape, Rules, When Unsure Policy, and 3 Few-Shot Examples.
- **Temperature**: `0.0` (Deterministic classification).

## 🛡️ Stage 3 Parsing, Validation, Repair, and Quarantine

Stage 3 implements robust error recovery and validation for LLM outputs.

### Key Logic Flow

1. **Markdown Stripping**: Clean raw model outputs by stripping \`\`\`json markdown wrappers.

2. **Schema Validation**: Validates cleaned JSON structure against the Pydantic `TriageResponse` schema.

3. **Single Repair Retry**: If Attempt 1 fails JSON decoding or schema validation, a repair message is sent back to the model with the rejection error details and raw output to attempt self-correction.

4. **Quarantine Logging**: If Attempt 2 repair fails, the failed attempt is logged to `logs/quarantine.jsonl` along with the timestamp, input text, error trace, and raw LLM output. The endpoint then returns an `HTTP 422 Unprocessable Entity` error.

## 🚀 Stage 4 Production Readiness (Timeouts, Retries, Cost Logging, Kill Switch)

Stage 4 makes the LLM endpoint fit to run in production under scale and failure conditions.

### 1. Real Timeout Enforcement (`30.0s`)

- Client request timeout is set explicitly to `30.0` seconds on the OpenAI client to prevent hanging connections.
- Unresolved timeouts raise a `TimeoutError` and map to `HTTP 504 Gateway Timeout`.

### 2. Explicit Retry Policy (Custom Exponential Backoff + Jitter)

- Default SDK retries are explicitly disabled (`max_retries=0`).
- Custom backoff with randomized jitter (1s, 2s, 4s + jitter) handles `429 Rate Limits` and `5xx Server Errors`.
- Respects `Retry-After` headers when provided by OpenRouter.
- Fast fails immediately on client errors (`400`, `401`, `403`) with zero retries.

### 3. Usage & Cost Metrics Logging (`logs/usage.jsonl`)

- Every model call writes structured JSON execution metrics to `logs/usage.jsonl`.
- Logs record: `timestamp`, `prompt_version`, `model`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `duration_ms`, and `needed_repair`.

### 4. Remote Kill Switch (`LLM_ENABLED`)

- Setting `LLM_ENABLED=false` in environment configuration immediately skips all model calls.
- Endpoint returns a clean `HTTP 503 Service Unavailable` error instantly without invoking OpenRouter.