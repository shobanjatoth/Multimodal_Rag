# import logging
# import os
# from typing import List, Dict, Union, AsyncGenerator
# from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
# import openai

# from app.llm.providers.base import LLMProvider
# from app.llm.providers.openai import OpenAIProvider
# from app.llm.providers.mock import MockProvider
# from app.memory.manager import ChatMessage

# logger = logging.getLogger(__name__)

# from app.core.config import get_settings

# settings = get_settings()

# class LLMGateway:
#     def __init__(self, provider_name: str = "openai"):
#         self.provider: LLMProvider = self._get_provider(provider_name)
        
#     def _get_provider(self, name: str) -> LLMProvider:
#         if name == "openai":
#             api_key = settings.OPENAI_API_KEY
#             base_url = settings.LLM_BASE_URL
            
#             # Strict check
#             if not api_key:
#                 logger.error("OPENAI_API_KEY is missing in settings!")
#                 raise ValueError("OPENAI_API_KEY is required.")
                
#             return OpenAIProvider(api_key=api_key, base_url=base_url, model=settings.LLM_MODEL)
#         elif name == "mock":
#             return MockProvider()
#         else:
#             raise ValueError(f"Unknown provider: {name}")

#     @retry(
#         stop=stop_after_attempt(3),
#         wait=wait_exponential(multiplier=1, min=2, max=10),
#         retry=retry_if_exception_type((openai.APIConnectionError, openai.RateLimitError)),
#         reraise=True
#     )
#     async def generate_response(self, messages: List[ChatMessage], **kwargs):
#         """
#         Generates a response with retry logic and unified monitoring.
#         """
#         # Convert internal ChatMessage model to provider dict format
#         msgs_dicts = [{"role": m.role.value, "content": m.content} for m in messages]
        
#         try:
#             response = await self.provider.generate_response(msgs_dicts, **kwargs)
            
#             # Simple Cost Tracking Hook
#             self._track_usage(response.usage)
            
#             return response.content
            
#         except Exception as e:
#             logger.error(f"LLM Generation failed: {e}")
#             raise

#     async def stream_response(self, messages: List[ChatMessage], **kwargs):
#         """
#         Streams response with retry logic.
#         """
#         msgs_dicts = [{"role": m.role.value, "content": m.content} for m in messages]
        
#         try:
#             async for chunk in self.provider.stream_response(msgs_dicts, **kwargs):
#                 if not chunk.content: 
#                     # Sometimes empty chunks come for finish reasons, which is fine
#                     continue
#                 yield chunk.content
#         except Exception as e:
#             logger.error(f"LLM Streaming Failed: {e}", exc_info=True)
#             yield f"\n[System Error: LLM Streaming Failed - {str(e)}]"
#             raise

#     def _track_usage(self, usage):
#         logger.info(f"Token Usage - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")
















import logging
from typing import List

import openai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.config import get_settings
from app.llm.providers.base import LLMProvider
from app.llm.providers.openai import GroqProvider
from app.llm.providers.mock import MockProvider
from app.llm.memory.manager import ChatMessage

logger = logging.getLogger(__name__)

settings = get_settings()


class LLMGateway:
    def __init__(self, provider_name: str = "groq"):
        self.provider: LLMProvider = self._get_provider(provider_name)

    def _get_provider(self, name: str) -> LLMProvider:
        if name == "groq":
            api_key = getattr(settings, "GROQ_API_KEY", None)
            model = getattr(
                settings,
                "GROQ_MODEL",
                "openai/gpt-oss-120b",
            )
            base_url = getattr(
                settings,
                "LLM_BASE_URL",
                "https://api.groq.com/openai/v1",
            )

            if not api_key:
                logger.error("GROQ_API_KEY is missing in settings.")
                raise ValueError(
                    "GROQ_API_KEY is required. Configure it in your .env file."
                )

            return GroqProvider(
                api_key=api_key,
                base_url=base_url,
                model=model,
            )

        elif name == "mock":
            return MockProvider()

        else:
            raise ValueError(f"Unknown provider: {name}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (
                openai.APIConnectionError,
                openai.RateLimitError,
            )
        ),
        reraise=True,
    )
    async def generate_response(
        self,
        messages: List[ChatMessage],
        **kwargs,
    ) -> str:
        """Generate a response with retry handling and usage logging."""

        msgs_dicts = [
            {
                "role": message.role.value,
                "content": message.content,
            }
            for message in messages
        ]

        try:
            response = await self.provider.generate_response(
                msgs_dicts,
                **kwargs,
            )

            self._track_usage(response.usage)

            return response.content

        except Exception as exc:
            logger.error("LLM generation failed: %s", exc)
            raise

    async def stream_response(
        self,
        messages: List[ChatMessage],
        **kwargs,
    ):
        """Stream the response from the configured provider."""

        msgs_dicts = [
            {
                "role": message.role.value,
                "content": message.content,
            }
            for message in messages
        ]

        try:
            async for chunk in self.provider.stream_response(
                msgs_dicts,
                **kwargs,
            ):
                if chunk.content:
                    yield chunk.content

        except Exception:
            logger.exception("LLM streaming failed")
            raise

    def _track_usage(self, usage):
        logger.info(
            "Token Usage - Prompt: %s, Completion: %s, Total: %s",
            usage.prompt_tokens,
            usage.completion_tokens,
            usage.total_tokens,
        )