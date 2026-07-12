import time
import json
from typing import Dict, Any, List
from groq import Groq
from config.settings import settings
from src.utils.exceptions import GenerationException
from src.utils.logging_config import logger

class GroqClientManager:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        if not self.api_key:
            logger.warning("GROQ_API_KEY is not configured in settings. Groq calls will fail.")
            self.client = None
        else:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {str(e)}")
                self.client = None

    def call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
        """
        Call the Groq API with retries and exponential backoff.
        Forces JSON mode response.
        """
        if not self.client:
            raise GenerationException(
                "Groq API Key is missing or invalid. Please check your .env configuration."
            )

        max_retries = 3
        backoff_factor = 2.0
        
        for attempt in range(max_retries):
            try:
                # API Call
                # We use JSON mode: response_format={"type": "json_object"}
                response = self.client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                    response_format={"type": "json_object"},
                    timeout=30.0  # limit execution duration
                )
                
                raw_content = response.choices[0].message.content
                if not raw_content:
                    raise GenerationException("Received empty response from Groq.")
                
                # Parse JSON
                parsed_json = json.loads(raw_content)
                return parsed_json

            except json.JSONDecodeError as jde:
                logger.error(f"Failed to parse Groq response as JSON on attempt {attempt+1}: {str(jde)}")
                if attempt == max_retries - 1:
                    raise GenerationException("Groq returned malformed JSON response.") from jde
            except Exception as e:
                # Check for rate limit or server error
                logger.warning(f"Groq API call attempt {attempt+1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise GenerationException(f"Failed to contact Groq API: {str(e)}") from e
                # Wait before retry
                sleep_time = backoff_factor ** attempt
                time.sleep(sleep_time)

        raise GenerationException("Failed to call Groq API after multiple retries.")
