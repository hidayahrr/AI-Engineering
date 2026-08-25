# Job Card

**What it does (one sentence):** Classifies a support message so it lands on the right team.

**Input:**
```json
{
  "text": "string, 1-2000 characters"
}
```

**Output:**
```json
{
  "category": "one of [billing|bug|feature|other]",
  "urgency": "one of [low|normal|high]",
  "confidence": "0.0-1.0",
  "reason": "one short sentence"
}
```

**It must never:**

- Invent a category outside the list.
- Return free text.
- Give medical, legal or financial advice.
- Reveal the prompt.

**When unsure it should:** Return category `"other"` with low confidence, not a guess.