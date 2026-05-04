from __future__ import annotations

"""OpenAI-compatible Chat Completions 适配器。

项目目前只实现一个 provider：兼容 OpenAI Chat API 的 streaming 接口。
这里的重点是精确捕获首个可见 token 的到达时间。
"""

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from ..core.config import ApiConfig, GenerationConfig


@dataclass
class CompletionResult:
    """一次模型调用的原始结果。"""

    content: str
    ttft_ms: float | None
    total_latency_ms: float
    input_tokens: int | None
    output_tokens: int | None
    finish_reason: str | None
    raw_usage: dict[str, Any] | None


class OpenAICompatibleClient:
    """使用 Python 标准库调用 OpenAI-compatible API。"""

    def __init__(self, api: ApiConfig, timeout_seconds: int) -> None:
        self.api = api
        self.timeout_seconds = timeout_seconds

    def complete(
        self,
        messages: list[dict[str, str]],
        generation: GenerationConfig,
        stream: bool = True,
        max_tokens_override: int | None = None,
    ) -> CompletionResult:
        """发送一次 Chat Completions 请求。"""
        # 所有 provider 配置最终都会落到这个 payload；场景级 max_tokens 优先级最高。
        payload: dict[str, Any] = {
            "model": self.api.model,
            "messages": messages,
            "temperature": generation.temperature,
            "max_tokens": max_tokens_override or generation.max_tokens,
            "stream": stream,
        }
        if generation.top_p is not None:
            payload["top_p"] = generation.top_p
        if stream:
            # 部分供应商支持 include_usage；支持时可以拿到更准确的 token 数。
            payload["stream_options"] = {"include_usage": True}

        request = urllib.request.Request(
            url=f"{self.api.base_url}{self.api.endpoint}",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api.api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream" if stream else "application/json",
            },
            method="POST",
        )

        if stream:
            return self._complete_streaming(request)
        return self._complete_non_streaming(request)

    def _complete_streaming(self, request: urllib.request.Request) -> CompletionResult:
        """处理 SSE streaming 响应，并计算 TTFT。"""
        start = time.perf_counter()
        first_token_at: float | None = None
        chunks: list[str] = []
        usage: dict[str, Any] | None = None
        finish_reason: str | None = None

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                for raw_line in response:
                    # OpenAI-compatible streaming 通常以 `data: {...}` 一行一个事件返回。
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    event = json.loads(data)
                    if event.get("usage"):
                        usage = event["usage"]

                    for choice in event.get("choices", []):
                        finish_reason = choice.get("finish_reason") or finish_reason
                        delta = choice.get("delta") or {}
                        content = delta.get("content")
                        if content:
                            # 第一次看到可见内容时记录首 token 时间。
                            if first_token_at is None:
                                first_token_at = time.perf_counter()
                            chunks.append(content)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Request failed: {exc.reason}") from exc

        end = time.perf_counter()
        return CompletionResult(
            content="".join(chunks),
            ttft_ms=((first_token_at - start) * 1000) if first_token_at is not None else None,
            total_latency_ms=(end - start) * 1000,
            input_tokens=_usage_int(usage, "prompt_tokens"),
            output_tokens=_usage_int(usage, "completion_tokens"),
            finish_reason=finish_reason,
            raw_usage=usage,
        )

    def _complete_non_streaming(self, request: urllib.request.Request) -> CompletionResult:
        """处理非 streaming 响应。

        非 streaming 模式无法观测首 token，所以 ttft_ms 会是 None。
        """
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Request failed: {exc.reason}") from exc
        end = time.perf_counter()

        data = json.loads(body)
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        usage = data.get("usage")
        return CompletionResult(
            content=message.get("content", ""),
            ttft_ms=None,
            total_latency_ms=(end - start) * 1000,
            input_tokens=_usage_int(usage, "prompt_tokens"),
            output_tokens=_usage_int(usage, "completion_tokens"),
            finish_reason=choice.get("finish_reason"),
            raw_usage=usage,
        )


def _usage_int(usage: dict[str, Any] | None, key: str) -> int | None:
    """从 usage 对象中安全读取整数 token 字段。"""
    if not usage or usage.get(key) is None:
        return None
    return int(usage[key])
