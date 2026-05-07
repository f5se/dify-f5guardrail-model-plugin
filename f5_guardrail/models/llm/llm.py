"""F5 Guardrail (CalypsoAI) LLM implementation for Dify.

The plugin sends Dify prompt messages through the F5 Guardrail ``prompts.send``
API. Guardrail forwards the prompt to the configured underlying LLM (selected
via ``provider`` and/or ``project``) and runs configured scanners on both the
prompt and the response. The plugin then converts the Guardrail outcome back
into Dify's ``LLMResult`` shape.

Limitations enforced by this plugin:

- **Streaming**: F5 Guardrail prompts API does not support streaming. When the
  caller requests stream mode, this plugin internally calls Guardrail in
  blocking mode and yields the result as a single ``LLMResultChunk`` so Dify's
  UI still works.
- **File uploads**: F5 Guardrail prompts API does not support file uploads.
  Any image/document/audio/video content in ``prompt_messages`` causes an
  ``InvokeBadRequestError`` to be raised with a clear message.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Generator
from typing import Any, Optional, Union

from dify_plugin.entities.model.llm import (
    LLMResult,
    LLMResultChunk,
    LLMResultChunkDelta,
)
from dify_plugin.entities.model.message import (
    AssistantPromptMessage,
    AudioPromptMessageContent,
    DocumentPromptMessageContent,
    ImagePromptMessageContent,
    PromptMessage,
    PromptMessageContentType,
    PromptMessageTool,
    SystemPromptMessage,
    TextPromptMessageContent,
    ToolPromptMessage,
    UserPromptMessage,
    VideoPromptMessageContent,
)
from dify_plugin.errors.model import (
    CredentialsValidateFailedError,
    InvokeAuthorizationError,
    InvokeBadRequestError,
    InvokeConnectionError,
    InvokeError,
    InvokeRateLimitError,
    InvokeServerUnavailableError,
)
from dify_plugin.interfaces.model.large_language_model import LargeLanguageModel
from utils.logging_control import is_plugin_log_enabled

logger = logging.getLogger(__name__)


DEFAULT_BLOCKED_TEMPLATE = "[F5 Guardrail] 请求被阻断：{reason}"


class F5GuardrailLargeLanguageModel(LargeLanguageModel):
    """LLM adapter that routes Dify chat traffic through F5 Guardrail."""

    def _invoke(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: Optional[list[PromptMessageTool]] = None,
        stop: Optional[list[str]] = None,
        stream: bool = True,
        user: Optional[str] = None,
    ) -> Union[LLMResult, Generator[LLMResultChunk, None, None]]:
        prompt_text = self._build_prompt_text(prompt_messages, credentials)
        guardrail_response = self._call_guardrail(
            credentials=credentials, prompt_text=prompt_text
        )
        outcome = self._extract_outcome(guardrail_response)
        response_text = self._extract_response_text(guardrail_response)
        scanner_summary = self._summarize_scanner_results(guardrail_response)

        if outcome != "cleared":
            return self._handle_blocked(
                model=model,
                credentials=credentials,
                prompt_messages=prompt_messages,
                prompt_text=prompt_text,
                outcome=outcome,
                scanner_summary=scanner_summary,
                stream=stream,
            )

        if stop:
            response_text = self.enforce_stop_tokens(response_text, stop)

        return self._build_success_result(
            model=model,
            credentials=credentials,
            prompt_messages=prompt_messages,
            prompt_text=prompt_text,
            response_text=response_text,
            stream=stream,
        )

    def get_num_tokens(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        tools: Optional[list[PromptMessageTool]] = None,
    ) -> int:
        text = self._build_prompt_text(
            prompt_messages, credentials, allow_multimodal_skip=True
        )
        return self._approximate_token_count(text)

    def validate_credentials(self, model: str, credentials: dict) -> None:
        try:
            self._build_client(credentials)
        except CredentialsValidateFailedError:
            raise
        except Exception as ex:
            raise CredentialsValidateFailedError(str(ex))

    @property
    def _invoke_error_mapping(self) -> dict[type[InvokeError], list[type[Exception]]]:
        return {
            InvokeConnectionError: [ConnectionError, TimeoutError],
            InvokeAuthorizationError: [PermissionError],
            InvokeBadRequestError: [ValueError, TypeError],
            InvokeServerUnavailableError: [],
            InvokeRateLimitError: [],
        }

    # ------------------------------------------------------------------
    # Prompt -> Guardrail text conversion
    # ------------------------------------------------------------------
    @staticmethod
    def _role_label(message: PromptMessage) -> str:
        if isinstance(message, SystemPromptMessage):
            return "System"
        if isinstance(message, UserPromptMessage):
            return "User"
        if isinstance(message, AssistantPromptMessage):
            return "Assistant"
        if isinstance(message, ToolPromptMessage):
            return "Tool"
        return getattr(message.role, "value", "User").capitalize()

    def _messages_to_text(
        self,
        prompt_messages: list[PromptMessage],
        allow_multimodal_skip: bool = False,
    ) -> str:
        # F5 Guardrail prompts API only accepts plain text. We merge all
        # messages into a role-tagged transcript so both the scanners and the
        # underlying LLM can see the full context.
        if not prompt_messages:
            return ""

        chunks: list[str] = []
        for message in prompt_messages:
            text = self._extract_text_from_message(
                message, allow_multimodal_skip=allow_multimodal_skip
            )
            if not text:
                continue
            chunks.append(f"[{self._role_label(message)}]\n{text}")
        return "\n\n".join(chunks).strip()

    def _build_prompt_text(
        self,
        prompt_messages: list[PromptMessage],
        credentials: dict,
        allow_multimodal_skip: bool = False,
    ) -> str:
        scope = (
            (credentials or {}).get("message_check_scope")
            or "full-conversation"
        ).strip().lower()
        if scope == "latest-user-message":
            return self._latest_user_message_to_text(
                prompt_messages, allow_multimodal_skip=allow_multimodal_skip
            )
        return self._messages_to_text(
            prompt_messages, allow_multimodal_skip=allow_multimodal_skip
        )

    def _latest_user_message_to_text(
        self,
        prompt_messages: list[PromptMessage],
        allow_multimodal_skip: bool = False,
    ) -> str:
        # New mode: only inspect the newest user message.
        for message in reversed(prompt_messages):
            if not isinstance(message, UserPromptMessage):
                continue
            text = self._extract_text_from_message(
                message, allow_multimodal_skip=allow_multimodal_skip
            ).strip()
            if text:
                return f"[User]\n{text}"
        raise InvokeBadRequestError(
            "No user message found for Guardrail check scope 'latest-user-message'."
        )

    @staticmethod
    def _extract_text_from_message(
        message: PromptMessage, allow_multimodal_skip: bool
    ) -> str:
        content = getattr(message, "content", None)
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if not isinstance(content, list):
            return str(content)

        text_parts: list[str] = []
        for item in content:
            if isinstance(item, TextPromptMessageContent):
                text_parts.append(item.data)
                continue
            if isinstance(
                item,
                (
                    ImagePromptMessageContent,
                    DocumentPromptMessageContent,
                    AudioPromptMessageContent,
                    VideoPromptMessageContent,
                ),
            ):
                if allow_multimodal_skip:
                    continue
                raise InvokeBadRequestError(
                    "F5 Guardrail prompts API does not support file/multimodal "
                    "uploads. Please remove image/document/audio/video content "
                    "from the request."
                )

            item_type = getattr(item, "type", None)
            if item_type == PromptMessageContentType.TEXT:
                text_parts.append(getattr(item, "data", ""))
            else:
                if allow_multimodal_skip:
                    continue
                raise InvokeBadRequestError(
                    f"Unsupported prompt content type for F5 Guardrail: {item_type}"
                )
        return "".join(text_parts)

    # ------------------------------------------------------------------
    # Guardrail SDK interaction
    # ------------------------------------------------------------------
    def _build_client(self, credentials: dict) -> Any:
        try:
            from calypsoai import CalypsoAI  # type: ignore[import-not-found]
        except ImportError as ex:
            raise InvokeBadRequestError(
                "F5 Guardrail SDK ('calypsoai') is not installed. "
                "Please install it inside the plugin runtime."
            ) from ex

        url = (credentials or {}).get("calypsoai_url", "").strip()
        token = (credentials or {}).get("calypsoai_token", "").strip()
        if not url or not token:
            raise CredentialsValidateFailedError(
                "Both 'calypsoai_url' and 'calypsoai_token' are required."
            )
        try:
            return CalypsoAI(url=url, token=token)
        except Exception as ex:
            raise self._map_exception(ex)

    def _call_guardrail(self, credentials: dict, prompt_text: str) -> Any:
        if not prompt_text:
            raise InvokeBadRequestError("Prompt text is empty after conversion.")

        client = self._build_client(credentials)

        kwargs: dict[str, Any] = {}
        provider = (credentials or {}).get("calypsoai_provider", "").strip()
        project = (credentials or {}).get("calypsoai_project", "").strip()
        if provider:
            kwargs["provider"] = provider
        if project:
            kwargs["project"] = project

        try:
            return client.prompts.send(prompt_text, **kwargs)
        except Exception as ex:
            raise self._map_exception(ex)

    # ------------------------------------------------------------------
    # Guardrail response parsing
    # ------------------------------------------------------------------
    @staticmethod
    def _to_dict(payload: Any) -> dict[str, Any]:
        if payload is None:
            return {}
        if isinstance(payload, dict):
            return payload
        for attr in ("model_dump", "dict"):
            if hasattr(payload, attr):
                try:
                    data = getattr(payload, attr)()
                    if isinstance(data, dict):
                        return data
                except Exception:
                    continue
        result: dict[str, Any] = {}
        for key in ("id", "input", "projectId", "provider", "result", "receivedAt"):
            if hasattr(payload, key):
                result[key] = getattr(payload, key)
        return result

    def _extract_outcome(self, payload: Any) -> str:
        data = self._to_dict(payload)
        result = data.get("result") or {}
        if not isinstance(result, dict):
            result = self._to_dict(result)
        outcome = (result.get("outcome") or "").strip().lower()
        return outcome or "unknown"

    def _extract_response_text(self, payload: Any) -> str:
        data = self._to_dict(payload)
        result = data.get("result") or {}
        if not isinstance(result, dict):
            result = self._to_dict(result)
        text = result.get("response")
        if isinstance(text, str):
            return text
        provider_result = result.get("providerResult") or {}
        if not isinstance(provider_result, dict):
            provider_result = self._to_dict(provider_result)
        return provider_result.get("data", "") or ""

    def _summarize_scanner_results(self, payload: Any) -> str:
        data = self._to_dict(payload)
        result = data.get("result") or {}
        if not isinstance(result, dict):
            result = self._to_dict(result)
        scanner_results = result.get("scannerResults") or []
        if not isinstance(scanner_results, list):
            return ""
        triggered: list[str] = []
        for item in scanner_results:
            if not isinstance(item, dict):
                item = self._to_dict(item)
            outcome = (item.get("outcome") or "").lower()
            if outcome and outcome != "passed":
                scanner_id = item.get("scannerId") or "unknown"
                direction = item.get("scanDirection") or "unknown"
                triggered.append(f"{scanner_id}({direction}):{outcome}")
        if triggered:
            return "scanners=" + ",".join(triggered)
        return f"outcome={result.get('outcome')}"

    # ------------------------------------------------------------------
    # Result construction
    # ------------------------------------------------------------------
    def _build_success_result(
        self,
        *,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        prompt_text: str,
        response_text: str,
        stream: bool,
    ) -> Union[LLMResult, Generator[LLMResultChunk, None, None]]:
        prompt_tokens = self._approximate_token_count(prompt_text)
        completion_tokens = self._approximate_token_count(response_text)
        usage = self._calc_response_usage(
            model=model,
            credentials=credentials,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        assistant_message = AssistantPromptMessage(content=response_text)

        if not stream:
            return LLMResult(
                model=model,
                prompt_messages=prompt_messages,
                message=assistant_message,
                usage=usage,
            )
        return self._yield_single_chunk(
            model=model,
            prompt_messages=prompt_messages,
            assistant_message=assistant_message,
            usage=usage,
            finish_reason="stop",
        )

    def _handle_blocked(
        self,
        *,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        prompt_text: str,
        outcome: str,
        scanner_summary: str,
        stream: bool,
    ) -> Union[LLMResult, Generator[LLMResultChunk, None, None]]:
        mode = (
            (credentials or {}).get("blocked_response_mode")
            or "message"
        ).strip().lower()
        template = (
            (credentials or {}).get("blocked_message_template")
            or DEFAULT_BLOCKED_TEMPLATE
        )
        reason = scanner_summary or outcome
        try:
            blocked_text = template.format(reason=reason, outcome=outcome)
        except Exception:
            blocked_text = f"[F5 Guardrail] 请求被阻断：{reason}"

        if is_plugin_log_enabled():
            logger.info(
                "F5 Guardrail blocked: outcome=%s summary=%s mode=%s",
                outcome,
                scanner_summary,
                mode,
            )

        if mode == "error":
            raise InvokeBadRequestError(blocked_text)

        prompt_tokens = self._approximate_token_count(prompt_text)
        completion_tokens = self._approximate_token_count(blocked_text)
        usage = self._calc_response_usage(
            model=model,
            credentials=credentials,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        assistant_message = AssistantPromptMessage(content=blocked_text)
        if not stream:
            return LLMResult(
                model=model,
                prompt_messages=prompt_messages,
                message=assistant_message,
                usage=usage,
            )
        return self._yield_single_chunk(
            model=model,
            prompt_messages=prompt_messages,
            assistant_message=assistant_message,
            usage=usage,
            finish_reason="stop",
        )

    @staticmethod
    def _yield_single_chunk(
        *,
        model: str,
        prompt_messages: list[PromptMessage],
        assistant_message: AssistantPromptMessage,
        usage,
        finish_reason: str,
    ) -> Generator[LLMResultChunk, None, None]:
        # F5 Guardrail does not support streaming. We deliver the full result
        # as one chunk with a terminal finish_reason so Dify's stream consumer
        # closes cleanly.
        yield LLMResultChunk(
            model=model,
            prompt_messages=prompt_messages,
            delta=LLMResultChunkDelta(
                index=0,
                message=assistant_message,
                usage=usage,
                finish_reason=finish_reason,
            ),
        )

    # ------------------------------------------------------------------
    # Misc helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _approximate_token_count(text: str) -> int:
        # Rough estimate: 1 token ~= 4 characters. Used only for cost / usage
        # display because Guardrail does not return tokenization data.
        if not text:
            return 0
        return max(1, len(text) // 4)

    def _map_exception(self, ex: Exception) -> InvokeError:
        message = str(ex)
        status_code = getattr(ex, "status_code", None) or getattr(
            ex, "status", None
        )
        if status_code is None:
            response = getattr(ex, "response", None)
            if response is not None:
                status_code = getattr(response, "status_code", None)

        lowered = message.lower()
        if status_code in (401, 403) or "unauthor" in lowered or "forbidden" in lowered:
            return InvokeAuthorizationError(message)
        if status_code == 429 or "rate limit" in lowered or "too many" in lowered:
            return InvokeRateLimitError(message)
        if status_code in (502, 503, 504) or "unavailable" in lowered:
            return InvokeServerUnavailableError(message)
        if status_code and 500 <= int(status_code) < 600:
            return InvokeServerUnavailableError(message)
        if "timeout" in lowered or "timed out" in lowered:
            return InvokeConnectionError(message)
        if "connection" in lowered:
            return InvokeConnectionError(message)
        if status_code and 400 <= int(status_code) < 500:
            return InvokeBadRequestError(message)
        return InvokeBadRequestError(message)

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)
