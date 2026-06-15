import json
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from groq import Groq

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DEFAULT_SYSTEM_PROMPT = (
    "You are a financial analysis assistant. "
    "Return clear, concise, structured outputs. "
    "When asked for JSON, return only valid JSON with no markdown."
)

JSON_SYSTEM_PROMPT = (
    "You are a financial analysis assistant. "
    "You must respond with a single valid JSON object only. "
    "Do not use markdown code fences. Do not add explanations before or after the JSON."
)


def _strip_markdown_fences(text: str) -> str:
    text = text.strip()
    if not text.startswith("```"):
        return text

    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    while lines and lines[-1].strip().startswith("```"):
        lines.pop()
    return "\n".join(lines).strip()


def _extract_json_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    quote_char = ""
    escape = False

    for i in range(start, len(text)):
        char = text[i]

        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quote_char:
                in_string = False
            continue

        if char in ('"', "'"):
            in_string = True
            quote_char = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    return None


def _parse_json_response(raw_response: str) -> dict:
    candidates = [
        raw_response.strip(),
        _strip_markdown_fences(raw_response),
    ]

    extracted = _extract_json_object(raw_response)
    if extracted:
        candidates.append(extracted)

    stripped = _strip_markdown_fences(raw_response)
    extracted_from_stripped = _extract_json_object(stripped)
    if extracted_from_stripped:
        candidates.append(extracted_from_stripped)

    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    raise json.JSONDecodeError("No valid JSON object found", raw_response, 0)


def ask_groq(prompt: str, system_prompt: Optional[str] = None, timeout: int = 30) -> str:
    if not prompt or not prompt.strip():
        return "Error: Prompt cannot be empty."

    api_key = os.getenv("GROQ_API_KEY") 

    if not api_key:
        return "Error: GROQ_API_KEY is missing. Set GROQ_API_KEY in .env file."

    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    try:
        client = Groq(api_key=api_key, timeout=timeout)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt or DEFAULT_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
            max_tokens=700,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        error_msg = str(e)
        if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
            return f"Error calling Groq API: Request timed out (check internet connection or API status)."
        return f"Error calling Groq API: {error_msg}"


def ask_groq_json(prompt: str, system_prompt: Optional[str] = None) -> dict:
    raw_response = ask_groq(prompt, system_prompt or JSON_SYSTEM_PROMPT)

    if raw_response.startswith("Error:"):
        return {"error": raw_response.removeprefix("Error:").strip()}

    try:
        return _parse_json_response(raw_response)

    except json.JSONDecodeError:
        return {
            "error": "Failed to parse LLM response as JSON",
            "raw_response": raw_response,
        }


if __name__ == "__main__":
    sample_prompt = """
Analyze the following stock metrics.

Return only valid JSON in this format:

{
  "stance": "Bullish | Bearish | Neutral",
  "confidence": 0,
  "reason": "Short explanation"
}

Metrics:
{
  "ticker": "TEST",
  "revenue_growth": 10.5,
  "debt_to_equity": 0.6,
  "roe": 25.0,
  "rsi": 58,
  "macd_signal": "positive",
  "price_above_sma50": true
}
"""

    print(ask_groq_json(sample_prompt))
