"""
Claude API client
Handles communication with Anthropic's Claude API
"""
import logging
import time
from typing import Optional, List, Dict
from anthropic import Anthropic, APIError, APIConnectionError


logger = logging.getLogger(__name__)


class ClaudeClient:
    """
    Claude API client wrapper
    """

    def __init__(self, api_key: str,
                 model: str = "claude-3-5-sonnet-20241022",
                 max_tokens: int = 500,
                 temperature: float = 0.7,
                 system_prompt: str = "You are a helpful assistant."):
        """
        Initialize Claude client

        Args:
            api_key: Anthropic API key
            model: Model name
            max_tokens: Maximum tokens in response
            temperature: Temperature for generation
            system_prompt: System prompt
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.system_prompt = system_prompt

    def send_message(self,
                    message: str,
                    conversation_history: List[Dict[str, str]] = None) -> tuple[Optional[str], Optional[int], Optional[str]]:
        """
        Send a message to Claude

        Args:
            message: User message
            conversation_history: Previous messages in conversation

        Returns:
            Tuple of (response_text, tokens_used, error_message)
        """
        start_time = time.time()

        try:
            # Build messages list
            messages = []

            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)

            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })

            # Call API
            logger.debug(f"Sending message to Claude: {message[:50]}...")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=messages
            )

            # Extract response text
            response_text = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    response_text += block.text

            # Get token usage
            tokens_used = None
            if hasattr(response, 'usage'):
                tokens_used = response.usage.input_tokens + response.usage.output_tokens

            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Claude response received ({elapsed_ms}ms, {tokens_used} tokens)")

            return response_text, tokens_used, None

        except APIConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(f"Claude API connection error: {e}")
            return None, None, error_msg

        except APIError as e:
            error_msg = f"API error: {str(e)}"
            logger.error(f"Claude API error: {e}")
            return None, None, error_msg

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error calling Claude: {e}")
            return None, None, error_msg

    def validate_api_key(self) -> bool:
        """
        Validate API key by making a test request

        Returns:
            True if API key is valid
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except APIError as e:
            logger.error(f"API key validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error validating API key: {e}")
            return False
