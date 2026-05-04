from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .core.config import AppConfig
from .core.metrics import RequestRecord, calculate_speed_metrics, summarize
from .core.token_counter import estimate_messages_tokens, estimate_tokens
from .providers.openai_compatible import OpenAICompatibleClient
from .reports.markdown import Reporter
from .scenarios.loader import Scenario, load_scenarios


class BenchmarkRunner:
    """benchmark 主编排器。

    Runner 不关心底层 HTTP 细节，也不负责报告排版。
    它只负责把「场景 -> 请求 -> 指标 -> 报告」这条链路串起来。
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.client = OpenAICompatibleClient(config.api, config.benchmark.timeout_seconds)

    def run(self) -> Path:
        # 场景从外部 JSON 文件加载，便于用户扩展自己的 agent 用例。
        scenarios = load_scenarios(self.config.scenarios, self.config.benchmark.scenarios_dir)
        records: list[RequestRecord] = []

        for scenario in scenarios:
            print(f"Running scenario: {scenario.name}")
            self._run_warmups(scenario)
            for run_id in range(1, self.config.benchmark.runs_per_scenario + 1):
                if scenario.kind == "multi_turn":
                    records.extend(self._run_multi_turn(scenario, run_id))
                else:
                    records.append(self._run_single_turn(scenario, run_id, round_id=None))

        summary_rows = summarize(records)
        reporter = Reporter(Path(self.config.benchmark.results_dir))
        return reporter.write_all(self.config, records, summary_rows)

    def _run_warmups(self, scenario: Scenario) -> None:
        """执行预热请求。

        预热结果不写入正式 records，用来降低冷启动、连接建立等噪声。
        """
        for warmup_id in range(1, self.config.benchmark.warmup_runs + 1):
            try:
                if scenario.kind == "multi_turn":
                    self._run_multi_turn(scenario, run_id=-warmup_id)
                else:
                    self._run_single_turn(scenario, run_id=-warmup_id, round_id=None)
            except Exception as exc:
                print(f"Warmup failed for {scenario.name}: {exc}")

    def _run_single_turn(self, scenario: Scenario, run_id: int, round_id: int | None) -> RequestRecord:
        """执行单轮场景。"""
        messages = [{"role": "user", "content": scenario.prompts[0]}]
        return self._execute_request(scenario, run_id, round_id, messages)

    def _run_multi_turn(self, scenario: Scenario, run_id: int) -> list[RequestRecord]:
        """执行多轮场景。

        每一轮都会把上一轮 assistant 的完整回复放回 messages，
        这样才能真实模拟上下文越来越重时的 agent 体验。
        """
        records: list[RequestRecord] = []
        messages: list[dict[str, str]] = []

        for index, prompt in enumerate(scenario.prompts, start=1):
            messages.append({"role": "user", "content": prompt})
            record = self._execute_request(scenario, run_id, index, messages)
            records.append(record)
            if record.success and record.assistant_content:
                messages.append({"role": "assistant", "content": record.assistant_content})
            elif record.success:
                messages.append({"role": "assistant", "content": ""})
            else:
                break
        return records

    def _execute_request(
        self,
        scenario: Scenario,
        run_id: int,
        round_id: int | None,
        messages: list[dict[str, str]],
    ) -> RequestRecord:
        """执行一次 API 请求，并把结果封装成 RequestRecord。"""
        created_at = datetime.now(timezone.utc).isoformat()
        try:
            result = self.client.complete(
                messages=messages,
                generation=self.config.generation,
                stream=self.config.benchmark.stream,
                max_tokens_override=scenario.max_tokens,
            )
            if not result.content.strip():
                raise RuntimeError("Empty visible assistant response.")
            # 优先使用供应商 usage 返回的 token 数；没有 usage 时再使用本地估算。
            output_tokens = result.output_tokens if result.output_tokens is not None else estimate_tokens(result.content)
            input_tokens = result.input_tokens if result.input_tokens is not None else estimate_messages_tokens(messages)
            # decode_tps 是首 token 之后的生成速度，比端到端 TPS 更接近模型持续输出能力。
            generation_time_ms, decode_tps, end_to_end_tps = calculate_speed_metrics(
                result.ttft_ms,
                result.total_latency_ms,
                output_tokens,
            )
            return RequestRecord(
                scenario=scenario.name,
                run_id=run_id,
                round_id=round_id,
                model=self.config.api.model,
                success=True,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                ttft_ms=result.ttft_ms,
                total_latency_ms=result.total_latency_ms,
                generation_time_ms=generation_time_ms,
                decode_tps=decode_tps,
                end_to_end_tps=end_to_end_tps,
                finish_reason=result.finish_reason,
                error=None,
                created_at=created_at,
                content_preview=result.content[:1000],
                assistant_content=result.content,
            )
        except Exception as exc:
            return RequestRecord(
                scenario=scenario.name,
                run_id=run_id,
                round_id=round_id,
                model=self.config.api.model,
                success=False,
                input_tokens=estimate_messages_tokens(messages),
                output_tokens=None,
                ttft_ms=None,
                total_latency_ms=None,
                generation_time_ms=None,
                decode_tps=None,
                end_to_end_tps=None,
                finish_reason=None,
                error=str(exc),
                created_at=created_at,
            )
