"""
LLM provider implementations for AI-powered remediation.

Architecture: each provider wraps its vendor SDK and exposes a uniform
generate_remediation(system_prompt, user_prompt) → str interface.

Providers use official SDKs (not raw httpx) for reliability:
- Anthropic: anthropic SDK (async client)
- OpenAI: openai SDK (async client)
- Google: google-genai SDK (async)
- Ollama: httpx POST to local inference server

BUILDER: implement each provider's generate_remediation() method.
The contracts, error handling patterns, and model configs are fully specified.
"""

import logging
from abc import ABC, abstractmethod

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers used in remediation and triage."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier string."""
        ...

    @abstractmethod
    async def generate_remediation(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate remediation guidance from the LLM.

        Args:
            system_prompt: System instructions (from prompts.py).
            user_prompt: Finding-specific context and question.

        Returns:
            Markdown-formatted remediation guidance.

        Raises:
            ProviderError: On API failures after retries.
        """
        ...


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude provider using the official anthropic SDK.

    Requirements:
    - pip install anthropic
    - ANTHROPIC_API_KEY env var set

    Usage pattern:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        message = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text
    """

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def generate_remediation(self, system_prompt: str, user_prompt: str) -> str:
        """Call Anthropic Claude to generate remediation guidance."""
        try:
            from anthropic import AsyncAnthropic
            import anthropic

            client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            message = await client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=2048,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return message.content[0].text
        except Exception as e:
            # Import here to avoid circular errors if anthropic not installed
            try:
                import anthropic as _a
                if isinstance(e, _a.RateLimitError):
                    import asyncio
                    logger.warning("Anthropic rate limited — waiting 10s")
                    await asyncio.sleep(10)
                    # One retry
                    client2 = _a.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
                    msg2 = await client2.messages.create(
                        model=settings.ANTHROPIC_MODEL,
                        max_tokens=2048,
                        system=system_prompt,
                        messages=[{"role": "user", "content": user_prompt}],
                    )
                    return msg2.content[0].text
            except Exception:
                pass
            logger.error("Anthropic provider error: %s", e)
            raise ProviderError("anthropic", str(e))


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI GPT provider using the official openai SDK.

    Requirements:
    - pip install openai
    - OPENAI_API_KEY env var set

    Usage pattern:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            max_tokens=2048,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content
    """

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate_remediation(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI GPT to generate remediation guidance."""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                max_tokens=2048,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("OpenAI provider error: %s", e)
            raise ProviderError("openai", str(e))


class GoogleProvider(BaseLLMProvider):
    """
    Google Gemini provider using the google-genai SDK.

    Requirements:
    - pip install google-genai
    - GOOGLE_AI_API_KEY env var set

    Usage pattern:
        from google import genai
        client = genai.Client(api_key=settings.GOOGLE_AI_API_KEY)
        response = await client.aio.models.generate_content(
            model=settings.GOOGLE_AI_MODEL,
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=2048,
            ),
        )
        return response.text
    """

    @property
    def provider_name(self) -> str:
        return "google"

    async def generate_remediation(self, system_prompt: str, user_prompt: str) -> str:
        """Call Google Gemini to generate remediation guidance."""
        try:
            from google import genai
            from google.genai import types as genai_types

            client = genai.Client(api_key=settings.GOOGLE_AI_API_KEY)
            response = await client.aio.models.generate_content(
                model=settings.GOOGLE_AI_MODEL,
                contents=user_prompt,
                config=genai_types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=2048,
                ),
            )
            return response.text or ""
        except Exception as e:
            logger.error("Google AI provider error: %s", e)
            raise ProviderError("google", str(e))


class OllamaProvider(BaseLLMProvider):
    """
    Self-hosted Ollama provider using httpx.

    No SDK needed — Ollama exposes an OpenAI-compatible REST API.

    Endpoint: POST {OLLAMA_BASE_URL}/api/chat
    Request body:
    {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": false
    }

    Response: {"message": {"content": "..."}}
    """

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def generate_remediation(self, system_prompt: str, user_prompt: str) -> str:
        """Call self-hosted Ollama to generate remediation guidance."""
        try:
            import httpx

            payload = {
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
            }
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                return response.json()["message"]["content"]
        except Exception as e:
            if "ConnectError" in type(e).__name__ or "connect" in str(e).lower():
                raise ProviderError("ollama", "Ollama not reachable — is it running?")
            logger.error("Ollama provider error: %s", e)
            raise ProviderError("ollama", str(e))


class ProviderError(Exception):
    """Raised when an LLM provider call fails."""

    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(f"[{provider}] {message}")
