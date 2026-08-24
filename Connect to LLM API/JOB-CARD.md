# 📋 Job Card: Support Ticket Classifier

> **Goal**: Classify incoming customer support messages into designated teams, assign an urgency score, measure confidence, and provide a short single-sentence justification.

---

## 📥 Input

| Field | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `text` | `string` | 1 – 2000 chars | Raw, unparsed customer support message |

---

## 📤 Output

```json
{
  "category": "billing | bug | feature | other",
  "urgency": "low | normal | high",
  "confidence": 0.0,
  "reason": "string"
}