"""Optional hosted MiniMax adapter; no SDK, Ollama or persisted credentials."""

from __future__ import annotations

import json
import re
import urllib.error
from urllib.parse import urlsplit

from .gateway import OpenAICompatibleGateway

DEFAULT_ENDPOINT = "https://api.minimax.io/v1"
DEFAULT_MODEL = "MiniMax-M3.1-Flash-Preview"


class MiniMaxError(ValueError):
    """Only locally constructed, credential-free diagnostic messages."""


class MiniMaxGateway(OpenAICompatibleGateway):
    """Reuse assessment/revision/validation with provider-specific wire format."""

    def __init__(self, *, api_key: str, endpoint: str = DEFAULT_ENDPOINT,
                 model: str = DEFAULT_MODEL, max_tokens: int = 8192, **kwargs) -> None:
        endpoint = endpoint.strip().rstrip("/")
        parsed = urlsplit(endpoint)
        if (parsed.scheme != "https" or parsed.hostname not in {"api.minimax.io", "api.minimaxi.com"}
                or parsed.path != "/v1" or parsed.username or parsed.password or parsed.query or parsed.fragment):
            raise ValueError("MiniMax base URL must be https://api.minimax.io/v1 or https://api.minimaxi.com/v1")
        if not api_key.strip() or not model.strip():
            raise ValueError("Enter a MiniMax API key and model name before running.")
        super().__init__(endpoint=endpoint, model=model.strip(), api_key=api_key.strip(),
                         max_tokens=max_tokens, **kwargs)
        self.provider_error = None

    def _chat(self, system: str, user: str, *, extra_messages: list[dict] | None = None) -> str:
        self.provider_error = None
        try:
            return self._request(system, user, extra_messages=extra_messages)
        except MiniMaxError as exc:
            self.provider_error = str(exc)
            raise

    def assess(self, criterion, evidence):
        draft = super().assess(criterion, evidence)
        if "provider_error" in draft.flags and self.provider_error:
            draft.explanation = f"Model request failed: {self.provider_error}. No AI score was produced."
        return draft

    def _request(self, system: str, user: str, *, extra_messages: list[dict] | None = None) -> str:
        # Ask for JSON in the existing prompt; do not assume JSON mode support.
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user},
                         *(extra_messages or [])],
            "max_completion_tokens": self.max_tokens,
            "reasoning_split": True,
        }
        if self.model == DEFAULT_MODEL:
            body["reasoning_effort"] = "low"
        try:
            raw = self._transport(f"{self.endpoint}/chat/completions",
                                  {"Content-Type": "application/json", "Authorization": f"Bearer {self._api_key}"},
                                  json.dumps(body).encode("utf-8"), self.timeout)
        except urllib.error.HTTPError as exc:
            # Never echo provider bodies, headers or credentials into the UI/log.
            hints = {400: "request parameters or model not supported", 401: "key authentication failed; check key and region",
                     403: "account/model permission denied", 404: "endpoint or model not found",
                     429: "rate limit or quota reached"}
            raise MiniMaxError(f"MiniMax HTTP {exc.code}: {hints.get(exc.code, 'provider request failed')}") from None
        data = json.loads(raw)
        status = data.get("base_resp", {}).get("status_code", 0)
        if status:
            # Only a numeric status is displayed; provider messages may contain secrets.
            safe_status = status if isinstance(status, int) else "unknown"
            raise MiniMaxError(f"MiniMax provider status {safe_status}; check account access, model and quota")
        choice = data["choices"][0]
        if choice.get("finish_reason") == "length":
            raise MiniMaxError("MiniMax output reached token limit; no score accepted")
        content = choice["message"].get("content")
        if not isinstance(content, str) or not content.strip():
            raise MiniMaxError("MiniMax returned no final text")
        # Some models include a leading thinking block even with reasoning_split.
        content = re.sub(r"^\s*<think>.*?</think>\s*", "", content, count=1, flags=re.S)
        return content

    @classmethod
    def from_env(cls, env=None, **kwargs):
        import os

        env = os.environ if env is None else env
        return cls(api_key=env.get("RMA_MINIMAX_API_KEY", ""),
                   endpoint=env.get("RMA_MINIMAX_ENDPOINT", DEFAULT_ENDPOINT),
                   model=env.get("RMA_MINIMAX_MODEL", DEFAULT_MODEL), **kwargs)
