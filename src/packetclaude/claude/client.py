"""
Claude API client
Handles communication with Anthropic's Claude API
"""
import logging
import time
import json
from typing import Optional, List, Dict, Any
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
                 system_prompt: str = "You are a helpful assistant.",
                 tools: Optional[List[Any]] = None):
        """
        Initialize Claude client

        Args:
            api_key: Anthropic API key
            model: Model name
            max_tokens: Maximum tokens in response
            temperature: Temperature for generation
            system_prompt: System prompt
            tools: List of tool objects (e.g., WebSearchTool)
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.tool_definitions = [tool.get_tool_definition() for tool in self.tools]

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

            # Call API with tool support
            logger.debug(f"Sending message to Claude: {message[:50]}...")

            # Prepare API call parameters
            api_params = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "system": self.system_prompt,
                "messages": messages
            }

            # Add tools if available
            if self.tool_definitions:
                api_params["tools"] = self.tool_definitions

            response = self.client.messages.create(**api_params)

            # Handle tool use (agentic loop)
            total_tokens = 0
            max_tool_iterations = 5
            iteration = 0

            while response.stop_reason == "tool_use" and iteration < max_tool_iterations:
                iteration += 1
                logger.debug(f"Tool use iteration {iteration}")

                # Track tokens
                if hasattr(response, 'usage'):
                    total_tokens += response.usage.input_tokens + response.usage.output_tokens

                # Process tool calls
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        tool_use_id = block.id

                        logger.info(f"Executing tool: {tool_name} with input: {tool_input}")

                        # Execute tool with error handling
                        try:
                            result = self._execute_tool(tool_name, tool_input)
                            logger.debug(f"Tool result: {result[:200]}...")
                        except Exception as e:
                            logger.error(f"Tool execution error: {e}", exc_info=True)
                            result = json.dumps({"error": f"Tool execution failed: {str(e)}"})

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": result
                        })

                # Add assistant message with tool use
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Add tool results
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # Continue conversation
                api_params["messages"] = messages
                response = self.client.messages.create(**api_params)

            # Extract final response text
            response_text = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    response_text += block.text

            # Get total token usage
            if hasattr(response, 'usage'):
                total_tokens += response.usage.input_tokens + response.usage.output_tokens

            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Claude response received ({elapsed_ms}ms, {total_tokens} tokens, {iteration} tool iterations)")

            return response_text, total_tokens, None

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

    def _execute_tool(self, tool_name: str, tool_input: Dict) -> str:
        """
        Execute a tool call

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tool result as string
        """
        for tool in self.tools:
            if hasattr(tool, 'execute_tool'):
                return tool.execute_tool(tool_name, tool_input)

        return f"Error: Tool '{tool_name}' not found"

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
