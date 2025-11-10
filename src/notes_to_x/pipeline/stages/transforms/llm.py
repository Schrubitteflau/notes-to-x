"""LLM calling via LiteLLM."""

import json
from typing import Literal

from litellm import completion
from pydantic import Field

from ...core import Context, Stage, StageOptions, register_stage
from ...core.helpers import require_context_keys


class LLMCallerOptions(StageOptions):
    """Options for LLMCaller stage."""

    model: str = Field(..., description="LLM model identifier (e.g., 'openai/gpt-4')")
    temperature: float = Field(default=0.2, description="Temperature for LLM sampling", ge=0.0, le=2.0)
    response_format: Literal["json", "text"] = Field(default="json", description="Expected response format")
    max_tokens: int | None = Field(default=None, description="Max tokens in response")
    mock: bool = Field(default=False, description="Use mock mode to skip actual LLM calls (for testing)")


@register_stage("llm.call")
class LLMCaller(Stage[LLMCallerOptions]):
    """
    Call LLM via LiteLLM and store response.

    REQUIRES: ctx.custom["system_prompt"], ctx.custom["user_message"]
    PRODUCES: ctx.note.results
    """

    Options = LLMCallerOptions

    @require_context_keys("system_prompt", "user_message")
    def execute(self, ctx: Context) -> Context:
        """Call LLM and store response."""
        # Get prompts from context (guaranteed by decorator)
        system_prompt = ctx.custom["system_prompt"]
        user_message = ctx.custom["user_message"]

        # Build LLM request
        model = self.options.model
        temperature = self.options.temperature
        max_tokens = self.options.max_tokens
        response_format = self.options.response_format

        # Mock mode: return fake data
        if self.options.mock:
            mock_response = self._generate_mock_response(ctx)
            ctx.note.results.append(mock_response)
            return ctx

        # Call LLM
        try:
            request_params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "temperature": temperature,
            }

            if max_tokens:
                request_params["max_tokens"] = max_tokens

            response = completion(**request_params)

            # Extract response content
            response_text = response["choices"][0]["message"]["content"]

            # Parse based on expected format
            if response_format == "json":
                try:
                    parsed_response = json.loads(response_text)
                    ctx.note.results.append(parsed_response)
                except json.JSONDecodeError as e:
                    ctx.add_issue(f"Failed to parse JSON response: {e}", self.name, severity="error")
                    ctx.note.results.append({"raw_output": response_text})
            else:
                ctx.note.results.append({"output": response_text})

        except Exception as e:
            ctx.add_issue(f"LLM call failed: {e}", self.name, severity="error")

        return ctx

    def _generate_mock_response(self, ctx: Context) -> dict:
        """Generate mock LLM response for testing."""
        # Extract some info from context for realistic mock data
        filename: str = ctx.file.name if ctx.file else "unknown.md"
        date = ctx.note.metadata.get("date", "01/01/2024")

        # Extract a snippet from the note content
        content: str = ctx.note.content[:100] if ctx.note.content else "Mock note content"

        return {
            "file": filename,
            "date": date,
            "results": [
                {
                    "summary": (
                        f"[MOCK] Extracted achievement from note (date: {date}).\n"
                        f"This is simulated output for testing without API calls. Content: {content}"
                    ),
                    "hard_skills": ["Python", "JavaScript", "API Design", "Testing"],
                    "soft_skills": ["Problem-solving", "Technical communication", "Time management"],
                }
            ],
        }
