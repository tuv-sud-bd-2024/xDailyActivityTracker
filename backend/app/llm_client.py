from .config import settings
from .schemas import LLMResponse, ParsedItem
from typing import Optional
import json


class BaseLLMClient:
    def parse_block(self, text: str) -> LLMResponse:
        raise NotImplementedError()


class NoopLLMClient(BaseLLMClient):
    def parse_block(self, text: str) -> LLMResponse:
        # Deterministic fallback: return empty parsed_items with the raw block
        return LLMResponse(source_block=text, parsed_items=[], overall_confidence=0.0)


class GeminiFlashClient(BaseLLMClient):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel("gemini-2.5-flash")
        except Exception as e:
            print(f"Failed to initialize Gemini: {e}")
            self.client = None

    def parse_block(self, text: str) -> LLMResponse:
        if not self.client:
            return NoopLLMClient().parse_block(text)

        try:
            prompt = f"""You are a JSON-only parser for WhatsApp activity messages. 
Parse the following WhatsApp message block and extract structured data.
Return ONLY valid JSON (no explanation) matching this exact schema:
{{
  "source_block": "<original text>",
  "parsed_items": [
    {{
      "item_id": "<string>",
      "source_sender": "<string>",
      "source_timestamp": "<ISO8601 datetime or null>",
      "activity_date": "<YYYY-MM-DD or null>",
      "start_time": "<HH:MM or null>",
      "end_time": "<HH:MM or null>",
      "description": "<string>",
      "is_client_activity": true or false,
      "client_candidates": [
        {{"client_name": "<string>", "client_match_score": <0.0-1.0>}}
      ],
      "deal_candidates": [
        {{"deal_name": "<string>", "deal_match_score": <0.0-1.0>}}
      ],
      "parsing_notes": "<string or null>",
      "confidence": <0.0-1.0>
    }}
  ],
  "overall_confidence": <0.0-1.0>
}}

Input message:
{text}

Return JSON only:"""

            response = self.client.generate_content(prompt)
            response_text = response.text.strip()
            
            # Try to extract JSON from response
            if response_text.startswith("```"):
                # Remove markdown code blocks if present
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            data = json.loads(response_text)
            return LLMResponse(**data)
        except json.JSONDecodeError as e:
            print(f"Gemini returned invalid JSON: {e}")
            return NoopLLMClient().parse_block(text)
        except Exception as e:
            print(f"Gemini parsing error: {e}")
            return NoopLLMClient().parse_block(text)


def get_llm_client() -> BaseLLMClient:
    if settings.GEMINI_API_KEY:
        try:
            return GeminiFlashClient()
        except Exception as e:
            print(f"Failed to create Gemini client: {e}, falling back to Noop")
            return NoopLLMClient()
    return NoopLLMClient()
