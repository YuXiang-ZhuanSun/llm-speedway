from __future__ import annotations

"""报告输出模块。

这里负责把 RequestRecord 写成三种产物：
Markdown 给人读，CSV 给表格工具读，JSONL 给排查和复现读。
"""

import csv
import json
from pathlib import Path
from typing import Any

from ..core.config import AppConfig
from ..core.metrics import RequestRecord


class Reporter:
    """把 benchmark 结果写入 results 目录。"""

    def __init__(self, results_dir: Path) -> None:
        self.results_dir = results_dir
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def write_all(
        self,
        config: AppConfig,
        records: list[RequestRecord],
        summary_rows: list[dict[str, Any]],
    ) -> Path:
        """一次性写出 raw、summary 和 Markdown 报告。"""
        self._write_raw(records)
        self._write_summary_csv(summary_rows)
        return self._write_markdown(config, summary_rows, records)

    def _write_raw(self, records: list[RequestRecord]) -> None:
        """写完整原始记录，方便后续复现和调试。"""
        path = self.results_dir / "raw_results.jsonl"
        with path.open("w", encoding="utf-8") as file:
            for record in records:
                file.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def _write_summary_csv(self, summary_rows: list[dict[str, Any]]) -> None:
        """写面向表格分析的精简 CSV。"""
        path = self.results_dir / "summary.csv"
        if not summary_rows:
            path.write_text("", encoding="utf-8")
            return

        fieldnames = [
            "scenario",
            "round_id",
            "runs",
            "success_rate",
            "ttft_ms_avg",
            "total_latency_ms_avg",
            "decode_tps_avg",
        ]
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for row in summary_rows:
                writer.writerow({key: row.get(key) for key in fieldnames})

    def _write_markdown(
        self,
        config: AppConfig,
        summary_rows: list[dict[str, Any]],
        records: list[RequestRecord],
    ) -> Path:
        """写面向人类决策的 Markdown 报告。"""
        path = self.results_dir / "report.md"
        successful_records = [record for record in records if record.success]
        overall_success = len(successful_records) / len(records) if records else 0

        lines = [
            f"# {config.api.model}",
            "",
            f"`{config.api.base_url}` | {config.benchmark.runs_per_scenario} run(s) per scenario | success {overall_success:.0%}",
            "",
            "## Read This First",
            "",
            _headline(summary_rows),
            "",
            "## Request Metrics",
            "",
            "| Scenario | Round | Start latency | Completion time | Generation speed |",
            "|---|---:|---:|---:|---:|",
        ]

        for row in summary_rows:
            lines.append(
                "| {scenario} | {round_id} | {ttft} | {total} | {decode} |".format(
                    scenario=row["scenario"],
                    round_id=row["round_id"] if row["round_id"] is not None else "-",
                    ttft=_fmt_ms(row.get("ttft_ms_avg")),
                    total=_fmt_ms(row.get("total_latency_ms_avg")),
                    decode=_fmt_tps(row.get("decode_tps_avg")),
                )
            )

        lines.extend(
            [
                "",
                "## How To Read",
                "",
                "- Start latency: user-visible waiting time before the model starts speaking.",
                "- Generation speed: generated tokens per second after the first token arrives.",
                "- Completion time: end-to-end time for the fixed scenario or round. Compare it only within the same prompt and settings.",
                "- multi_turn: a sequence of requests carrying previous conversation history, used to expose context-growth slowdown.",
            ]
        )

        errors = [record for record in records if not record.success]
        if errors:
            lines.extend(["", "## Errors", ""])
            for record in errors[:20]:
                lines.append(f"- `{record.scenario}` run `{record.run_id}` round `{record.round_id}`: {record.error}")
            if len(errors) > 20:
                lines.append(f"- ... and {len(errors) - 20} more errors.")

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path


def _headline(summary_rows: list[dict[str, Any]]) -> str:
    """生成报告开头的一句话摘要。"""
    short = _find_row(summary_rows, "short_chat", None)
    long = _find_row(summary_rows, "long_generation", None)
    multi_rows = [row for row in summary_rows if row.get("scenario") == "multi_turn" and row.get("success_rate", 0) > 0]
    last_multi = multi_rows[-1] if multi_rows else None

    parts: list[str] = []
    if short and short.get("success_rate", 0) > 0:
        parts.append(f"Short chat starts in {_fmt_ms(short.get('ttft_ms_avg'))}.")
    if long and long.get("success_rate", 0) > 0:
        parts.append(f"Long generation runs at {_fmt_tps(long.get('decode_tps_avg'))}.")
    if last_multi:
        parts.append(f"By the last multi-turn round, completion time is {_fmt_ms(last_multi.get('total_latency_ms_avg'))}.")
    if not parts:
        return "No successful samples were collected."
    return " ".join(parts)


def _find_row(summary_rows: list[dict[str, Any]], scenario: str, round_id: int | None) -> dict[str, Any] | None:
    """查找指定场景和轮次的汇总行。"""
    for row in summary_rows:
        if row.get("scenario") == scenario and row.get("round_id") == round_id:
            return row
    return None


def _fmt_ms(value: Any) -> str:
    """毫秒转成秒显示。"""
    if value is None:
        return "-"
    return f"{float(value) / 1000:.2f}s"


def _fmt_tps(value: Any) -> str:
    """格式化 tokens/s。"""
    if value is None:
        return "-"
    return f"{float(value):.1f} tok/s"
