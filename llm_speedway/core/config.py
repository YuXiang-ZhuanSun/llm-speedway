from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ApiConfig:
    base_url: str
    api_key: str
    model: str
    endpoint: str = "/chat/completions"


@dataclass
class BenchmarkConfig:
    runs_per_scenario: int = 5
    timeout_seconds: int = 120
    warmup_runs: int = 1
    stream: bool = True
    results_dir: str = "results"


@dataclass
class GenerationConfig:
    temperature: float = 0.7
    max_tokens: int = 512
    top_p: float | None = None


@dataclass
class AppConfig:
    api: ApiConfig
    benchmark: BenchmarkConfig = field(default_factory=BenchmarkConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    scenarios: list[str] = field(default_factory=lambda: ["short_chat", "long_generation", "multi_turn"])


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    raw = _load_raw_config(path)
    return parse_config(raw)


def _load_raw_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(text)
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise RuntimeError("YAML config requires PyYAML. Use config.example.json or install PyYAML.") from exc
        loaded = yaml.safe_load(text)
        if not isinstance(loaded, dict):
            raise ValueError("Config root must be a mapping.")
        return loaded
    raise ValueError("Unsupported config format. Use .json, .yaml, or .yml.")


def parse_config(raw: dict[str, Any]) -> AppConfig:
    api_raw = raw.get("api") or {}
    if not api_raw.get("base_url"):
        raise ValueError("api.base_url is required.")
    api_key = _resolve_api_key(api_raw)
    if not api_key:
        raise ValueError("api.api_key or api.api_key_env is required.")
    if not api_raw.get("model"):
        raise ValueError("api.model is required.")

    benchmark_raw = raw.get("benchmark") or {}
    generation_raw = raw.get("generation") or {}

    return AppConfig(
        api=ApiConfig(
            base_url=str(api_raw["base_url"]).rstrip("/"),
            api_key=api_key,
            model=str(api_raw["model"]),
            endpoint=_normalize_endpoint(str(api_raw.get("endpoint", "/chat/completions"))),
        ),
        benchmark=BenchmarkConfig(
            runs_per_scenario=int(benchmark_raw.get("runs_per_scenario", 5)),
            timeout_seconds=int(benchmark_raw.get("timeout_seconds", 120)),
            warmup_runs=int(benchmark_raw.get("warmup_runs", 1)),
            stream=bool(benchmark_raw.get("stream", True)),
            results_dir=str(benchmark_raw.get("results_dir", "results")),
        ),
        generation=GenerationConfig(
            temperature=float(generation_raw.get("temperature", 0.7)),
            max_tokens=int(generation_raw.get("max_tokens", 512)),
            top_p=_optional_float(generation_raw.get("top_p")),
        ),
        scenarios=list(raw.get("scenarios") or ["short_chat", "long_generation", "multi_turn"]),
    )


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _resolve_api_key(api_raw: dict[str, Any]) -> str:
    api_key = str(api_raw.get("api_key") or "").strip()
    if api_key:
        return api_key

    env_name = str(api_raw.get("api_key_env") or "").strip()
    if env_name:
        return os.environ.get(env_name, "").strip()
    return ""


def _normalize_endpoint(endpoint: str) -> str:
    endpoint = endpoint.strip()
    if not endpoint:
        return "/chat/completions"
    if not endpoint.startswith("/"):
        return f"/{endpoint}"
    return endpoint
