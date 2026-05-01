from __future__ import annotations

"""测试用例加载器。

项目把 benchmark 用例放在根目录 `scenarios/` 下，而不是写死在 Python 代码里。
这样新增用例时只需要增加一个 JSON 文件，并在 config 的 `scenarios` 列表里引用它。
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Scenario:
    """一次 benchmark 场景的结构化定义。"""

    name: str
    description: str
    # single_turn 表示每次请求独立；multi_turn 表示后续轮次携带历史上下文。
    kind: str
    prompts: list[str]
    # 场景级 max_tokens 可以覆盖全局 generation.max_tokens，保证不同场景输出长度可控。
    max_tokens: int | None = None


def load_scenarios(names: list[str], scenarios_dir: str = "scenarios") -> list[Scenario]:
    """按配置顺序加载多个场景。

    `names` 里的每一项既可以是场景名，例如 `short_chat`，
    也可以是具体 JSON 路径，例如 `custom/my_case.json`。
    """
    root = Path(scenarios_dir)
    scenarios: list[Scenario] = []
    for name in names:
        scenarios.append(load_scenario(name, root))
    return scenarios


def load_scenario(name_or_path: str, scenarios_dir: Path) -> Scenario:
    """加载单个场景 JSON，并转成强类型 Scenario。"""
    path = _resolve_scenario_path(name_or_path, scenarios_dir)
    if not path.exists():
        available = ", ".join(_available_scenarios(scenarios_dir)) or "none"
        raise ValueError(f"Unknown scenario '{name_or_path}'. Available scenarios: {available}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Scenario file must contain a JSON object: {path}")
    return parse_scenario(raw, source=path)


def parse_scenario(raw: dict[str, Any], source: Path | None = None) -> Scenario:
    """校验场景字段，避免无效用例在运行中才失败。"""
    label = str(source) if source else str(raw.get("name", "<memory>"))
    name = str(raw.get("name") or "").strip()
    kind = str(raw.get("kind") or "").strip()
    prompts = raw.get("prompts")

    if not name:
        raise ValueError(f"Scenario missing required field 'name': {label}")
    if kind not in {"single_turn", "multi_turn"}:
        raise ValueError(f"Scenario '{name}' has invalid kind '{kind}'. Use single_turn or multi_turn.")
    if not isinstance(prompts, list) or not prompts or not all(isinstance(item, str) and item.strip() for item in prompts):
        raise ValueError(f"Scenario '{name}' requires a non-empty string list field 'prompts'.")

    max_tokens = raw.get("max_tokens")
    return Scenario(
        name=name,
        description=str(raw.get("description") or ""),
        kind=kind,
        prompts=[item.strip() for item in prompts],
        max_tokens=int(max_tokens) if max_tokens is not None else None,
    )


def _resolve_scenario_path(name_or_path: str, scenarios_dir: Path) -> Path:
    """把场景名解析为 JSON 文件路径。"""
    candidate = Path(name_or_path)
    if candidate.suffix.lower() == ".json" or len(candidate.parts) > 1:
        return candidate
    return scenarios_dir / f"{name_or_path}.json"


def _available_scenarios(scenarios_dir: Path) -> list[str]:
    """列出用例目录里可用的场景名，用于错误提示。"""
    if not scenarios_dir.exists():
        return []
    return sorted(path.stem for path in scenarios_dir.glob("*.json"))

