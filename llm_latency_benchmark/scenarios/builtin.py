from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    kind: str
    prompts: list[str]
    max_tokens: int | None = None


BUILTIN_SCENARIOS: dict[str, Scenario] = {
    "short_chat": Scenario(
        name="short_chat",
        description="短对话：轻量问答，观察首 token 和短输出总延迟。",
        kind="single_turn",
        prompts=["请严格用三句话解释什么是机器学习。"],
        max_tokens=256,
    ),
    "long_generation": Scenario(
        name="long_generation",
        description="长输出：观察持续生成速度和长响应稳定性。",
        kind="single_turn",
        prompts=["请写一篇 1000 字左右的文章，主题是人工智能对软件工程的影响。"],
        max_tokens=1024,
    ),
    "multi_turn": Scenario(
        name="multi_turn",
        description="多轮对话：观察上下文增长后的首 token 和生成速度变化。",
        kind="multi_turn",
        prompts=[
            "我想开发一个笔记应用，帮我设计核心功能。",
            "如果加入 AI 总结功能，应该怎么设计？",
            "帮我拆成 MVP、v1、v2 三个阶段。",
            "如果我要做订阅收费，应该有哪些限制？",
            "请总结成产品需求文档。",
        ],
        max_tokens=512,
    ),
}


def load_scenarios(names: list[str]) -> list[Scenario]:
    scenarios: list[Scenario] = []
    for name in names:
        if name not in BUILTIN_SCENARIOS:
            known = ", ".join(sorted(BUILTIN_SCENARIOS))
            raise ValueError(f"Unknown scenario '{name}'. Built-in scenarios: {known}")
        scenarios.append(BUILTIN_SCENARIOS[name])
    return scenarios
