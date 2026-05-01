from __future__ import annotations

"""指标数据结构与统计函数。

报告只展示三个指标，但原始记录保留更多字段，
这样既能保持 README 和报告清爽，也能在需要时回溯细节。
"""

from dataclasses import dataclass, field
from statistics import mean
from typing import Any


@dataclass
class RequestRecord:
    """一次 API 请求对应的一条原始记录。"""

    scenario: str
    run_id: int
    round_id: int | None
    model: str
    success: bool
    input_tokens: int | None
    output_tokens: int | None
    ttft_ms: float | None
    total_latency_ms: float | None
    generation_time_ms: float | None
    decode_tps: float | None
    end_to_end_tps: float | None
    finish_reason: str | None
    error: str | None
    created_at: str
    content_preview: str = field(default="")
    assistant_content: str = field(default="", repr=False)

    def to_dict(self) -> dict[str, Any]:
        """转成可写入 JSONL 的 dict。

        assistant_content 可能很长，只用于多轮上下文传递，不写入公开报告。
        """
        return {
            "scenario": self.scenario,
            "run_id": self.run_id,
            "round_id": self.round_id,
            "model": self.model,
            "success": self.success,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "ttft_ms": _round_or_none(self.ttft_ms),
            "total_latency_ms": _round_or_none(self.total_latency_ms),
            "generation_time_ms": _round_or_none(self.generation_time_ms),
            "decode_tps": _round_or_none(self.decode_tps),
            "end_to_end_tps": _round_or_none(self.end_to_end_tps),
            "finish_reason": self.finish_reason,
            "error": self.error,
            "created_at": self.created_at,
            "content_preview": self.content_preview,
        }


def calculate_speed_metrics(
    ttft_ms: float | None,
    total_latency_ms: float,
    output_tokens: int,
) -> tuple[float | None, float | None, float | None]:
    """根据首 token、总耗时和输出 token 数计算速度指标。"""
    generation_time_ms = None
    decode_tps = None
    if ttft_ms is not None:
        # 生成阶段耗时 = 总耗时 - 首 token 等待时间。
        generation_time_ms = max(total_latency_ms - ttft_ms, 0.0)
        if generation_time_ms > 0:
            decode_tps = output_tokens / (generation_time_ms / 1000)

    end_to_end_tps = None
    if total_latency_ms > 0:
        end_to_end_tps = output_tokens / (total_latency_ms / 1000)

    return generation_time_ms, decode_tps, end_to_end_tps


def summarize(records: list[RequestRecord]) -> list[dict[str, Any]]:
    """按 scenario + round 聚合多次运行结果。"""
    groups: dict[tuple[str, int | None], list[RequestRecord]] = {}
    for record in records:
        key = (record.scenario, record.round_id)
        groups.setdefault(key, []).append(record)

    rows: list[dict[str, Any]] = []
    for (scenario, round_id), group_records in sorted(groups.items(), key=lambda item: (item[0][0], item[0][1] or 0)):
        successes = [record for record in group_records if record.success]
        row: dict[str, Any] = {
            "scenario": scenario,
            "round_id": round_id,
            "runs": len(group_records),
            "successes": len(successes),
            "success_rate": len(successes) / len(group_records) if group_records else 0,
        }
        for field_name in [
            "ttft_ms",
            "total_latency_ms",
            "generation_time_ms",
            "decode_tps",
            "end_to_end_tps",
            "input_tokens",
            "output_tokens",
        ]:
            values = [getattr(record, field_name) for record in successes if getattr(record, field_name) is not None]
            row.update(_stats(field_name, [float(value) for value in values]))
        rows.append(row)
    return rows


def _stats(prefix: str, values: list[float]) -> dict[str, float | None]:
    """计算平均值、分位数、最小值和最大值。"""
    if not values:
        return {
            f"{prefix}_avg": None,
            f"{prefix}_p50": None,
            f"{prefix}_p90": None,
            f"{prefix}_p95": None,
            f"{prefix}_min": None,
            f"{prefix}_max": None,
        }
    sorted_values = sorted(values)
    return {
        f"{prefix}_avg": round(mean(sorted_values), 3),
        f"{prefix}_p50": round(_percentile(sorted_values, 50), 3),
        f"{prefix}_p90": round(_percentile(sorted_values, 90), 3),
        f"{prefix}_p95": round(_percentile(sorted_values, 95), 3),
        f"{prefix}_min": round(sorted_values[0], 3),
        f"{prefix}_max": round(sorted_values[-1], 3),
    }


def _percentile(sorted_values: list[float], percentile: float) -> float:
    """线性插值分位数。"""
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (len(sorted_values) - 1) * percentile / 100
    lower = int(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = rank - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def _round_or_none(value: float | None) -> float | None:
    """统一保留三位小数。"""
    if value is None:
        return None
    return round(value, 3)
