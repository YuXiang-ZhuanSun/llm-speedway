from __future__ import annotations

"""轻量 token 估算器。

供应商 usage 字段最准确；只有当接口不返回 usage 时，才会使用这里的估算。
估算值用于相对 benchmark，不用于账单级统计。
"""

import re

_CJK_RE = re.compile(r"[\u3400-\u9fff]")
_WORD_OR_SYMBOL_RE = re.compile(r"[A-Za-z0-9_]+|[^\w\s]", re.UNICODE)


def estimate_tokens(text: str) -> int:
    """A lightweight fallback token estimator.

    It is intentionally conservative enough for relative latency benchmarks.
    Provider usage fields are preferred whenever available.
    """
    if not text:
        return 0
    cjk_count = len(_CJK_RE.findall(text))
    without_cjk = _CJK_RE.sub(" ", text)
    word_symbol_count = len(_WORD_OR_SYMBOL_RE.findall(without_cjk))
    return max(1, cjk_count + word_symbol_count)


def estimate_messages_tokens(messages: list[dict[str, str]]) -> int:
    """估算多条 chat messages 的输入 token 数。"""
    content_tokens = sum(estimate_tokens(message.get("content", "")) for message in messages)
    return content_tokens + len(messages) * 4
