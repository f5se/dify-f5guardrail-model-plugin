"""Smoke tests that exercise the F5 Guardrail LLM adapter without the real SDK.

We monkey-patch ``F5GuardrailLargeLanguageModel._build_client`` so the tests do
not require the proprietary ``calypsoai`` package or network access.
"""

from __future__ import annotations

import os
import sys
import time
from decimal import Decimal
from typing import Any

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from dify_plugin.entities.model.llm import LLMUsage  # noqa: E402
from dify_plugin.entities.model.message import (  # noqa: E402
    AssistantPromptMessage,
    DocumentPromptMessageContent,
    PromptMessage,
    SystemPromptMessage,
    UserPromptMessage,
)
from dify_plugin.errors.model import InvokeBadRequestError  # noqa: E402

from models.llm.llm import F5GuardrailLargeLanguageModel  # noqa: E402


def _fake_usage(**kwargs) -> LLMUsage:
    prompt_tokens = kwargs.get("prompt_tokens", 0)
    completion_tokens = kwargs.get("completion_tokens", 0)
    zero = Decimal("0")
    return LLMUsage(
        prompt_tokens=prompt_tokens,
        prompt_unit_price=zero,
        prompt_price_unit=zero,
        prompt_price=zero,
        completion_tokens=completion_tokens,
        completion_unit_price=zero,
        completion_price_unit=zero,
        completion_price=zero,
        total_tokens=prompt_tokens + completion_tokens,
        total_price=zero,
        currency="USD",
        latency=0.01,
    )


def _credentials(**overrides: Any) -> dict:
    base = {
        "calypsoai_url": "https://www.us1.calypsoai.app",
        "calypsoai_token": "fake-token",
        "calypsoai_provider": "demo-provider",
        "calypsoai_project": "demo-project",
        "message_check_scope": "full-conversation",
        "blocked_response_mode": "message",
        "blocked_message_template": "[F5 Guardrail] blocked: {reason}",
    }
    base.update(overrides)
    return base


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def model_dump(self) -> dict:
        return self._payload


class _FakePromptsAPI:
    def __init__(self, response: _FakeResponse):
        self._response = response
        self.calls: list[tuple[str, dict]] = []

    def send(self, prompt: str, **kwargs):
        self.calls.append((prompt, dict(kwargs)))
        return self._response


class _FakeClient:
    def __init__(self, response: _FakeResponse):
        self.prompts = _FakePromptsAPI(response)


def _patched_model(monkeypatch: pytest.MonkeyPatch, response_payload: dict):
    fake_client = _FakeClient(_FakeResponse(response_payload))
    model = F5GuardrailLargeLanguageModel(model_schemas=[])
    monkeypatch.setattr(model, "_build_client", lambda creds: fake_client)
    monkeypatch.setattr(model, "_calc_response_usage", lambda **kwargs: _fake_usage(**kwargs))
    model.started_at = time.perf_counter()
    return model, fake_client


def test_cleared_outcome_returns_assistant_text(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "id": "p-1",
        "input": "hi",
        "result": {
            "outcome": "cleared",
            "response": "hello there",
            "scannerResults": [
                {"outcome": "passed", "scanDirection": "request", "scannerId": "s1"}
            ],
        },
    }
    model, client = _patched_model(monkeypatch, payload)
    result = model._invoke(
        model="f5-guardrail",
        credentials=_credentials(),
        prompt_messages=[UserPromptMessage(content="hi")],
        model_parameters={},
        stream=False,
    )
    assert result.message.content == "hello there"
    assert client.prompts.calls[0][1] == {
        "provider": "demo-provider",
        "project": "demo-project",
    }


def test_blocked_message_mode_returns_blocked_text(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "result": {
            "outcome": "blocked",
            "response": None,
            "scannerResults": [
                {"outcome": "flagged", "scanDirection": "request", "scannerId": "pii"}
            ],
        }
    }
    model, _ = _patched_model(monkeypatch, payload)
    result = model._invoke(
        model="f5-guardrail",
        credentials=_credentials(blocked_response_mode="message"),
        prompt_messages=[UserPromptMessage(content="leak my data")],
        model_parameters={},
        stream=False,
    )
    assert "blocked" in result.message.content
    assert "pii(request):flagged" in result.message.content


def test_blocked_error_mode_raises(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "result": {
            "outcome": "blocked",
            "scannerResults": [
                {"outcome": "flagged", "scanDirection": "request", "scannerId": "pii"}
            ],
        }
    }
    model, _ = _patched_model(monkeypatch, payload)
    with pytest.raises(InvokeBadRequestError):
        model._invoke(
            model="f5-guardrail",
            credentials=_credentials(blocked_response_mode="error"),
            prompt_messages=[UserPromptMessage(content="leak my data")],
            model_parameters={},
            stream=False,
        )


def test_stream_request_yields_single_chunk(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "result": {
            "outcome": "cleared",
            "response": "ok",
            "scannerResults": [],
        }
    }
    model, _ = _patched_model(monkeypatch, payload)
    gen = model._invoke(
        model="f5-guardrail",
        credentials=_credentials(),
        prompt_messages=[UserPromptMessage(content="hi")],
        model_parameters={},
        stream=True,
    )
    chunks = list(gen)
    assert len(chunks) == 1
    assert chunks[0].delta.message.content == "ok"
    assert chunks[0].delta.finish_reason == "stop"


def test_file_upload_raises_invoke_bad_request(monkeypatch: pytest.MonkeyPatch):
    payload = {"result": {"outcome": "cleared", "response": "ok"}}
    model, _ = _patched_model(monkeypatch, payload)
    multimodal = UserPromptMessage(
        content=[
            DocumentPromptMessageContent(
                format="pdf",
                base64_data="aGVsbG8=",
                mime_type="application/pdf",
                filename="x.pdf",
            )
        ]
    )
    with pytest.raises(InvokeBadRequestError):
        model._invoke(
            model="f5-guardrail",
            credentials=_credentials(),
            prompt_messages=[multimodal],
            model_parameters={},
            stream=False,
        )


def test_message_to_text_includes_role_labels():
    model = F5GuardrailLargeLanguageModel(model_schemas=[])
    text = model._messages_to_text(
        [
            SystemPromptMessage(content="be nice"),
            UserPromptMessage(content="hello"),
            AssistantPromptMessage(content="hi"),
            UserPromptMessage(content="how are you"),
        ]
    )
    assert "[System]\nbe nice" in text
    assert "[User]\nhello" in text
    assert "[Assistant]\nhi" in text
    assert text.endswith("how are you")


def test_latest_user_message_scope_only_sends_latest_user(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "result": {
            "outcome": "cleared",
            "response": "ok",
            "scannerResults": [],
        }
    }
    model, client = _patched_model(monkeypatch, payload)
    model._invoke(
        model="f5-guardrail",
        credentials=_credentials(message_check_scope="latest-user-message"),
        prompt_messages=[
            SystemPromptMessage(content="be safe"),
            UserPromptMessage(content="first user"),
            AssistantPromptMessage(content="assistant"),
            UserPromptMessage(content="latest user"),
        ],
        model_parameters={},
        stream=False,
    )
    sent_prompt = client.prompts.calls[0][0]
    assert sent_prompt == "[User]\nlatest user"


def test_latest_user_message_scope_without_user_raises():
    model = F5GuardrailLargeLanguageModel(model_schemas=[])
    with pytest.raises(InvokeBadRequestError):
        model._build_prompt_text(
            [SystemPromptMessage(content="only system")],
            credentials={"message_check_scope": "latest-user-message"},
        )
