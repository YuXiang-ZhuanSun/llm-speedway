# llm-speedway Public Benchmark Reports

All runs use the same request-level metrics:

- Start latency: `ttft_ms`, time until the first visible assistant token.
- Generation speed: `decode_tps`, tokens per second after the first token.
- Completion time: `total_latency_ms`, end-to-end time for the same fixed scenario or round.

Scenario names are not metrics. `multi_turn` is a context-accumulation test: each round is a new request that carries previous conversation history.

| Model | Start latency on `short_chat` | Generation speed on `long_generation` | `multi_turn` context test | Report |
|---|---:|---:|---|---|
| `deepseek-v4-flash` | 6.33s | 97.6 tok/s | success | [report](deepseek-v4-flash/report.md) |
| `doubao-seed-2.0-code` | 15.31s | 105.1 tok/s | success | [report](ark-doubao-seed-2-code/report.md) |
| `glm-5.1` | 24.56s | 76.5 tok/s | failed on round 1 | [report](ark-glm-5-1/report.md) |
| `kimi-k2.6` | 11.88s | 68.3 tok/s | empty visible response on round 1 | [report](ark-kimi-k2-6/report.md) |

Completion time is a scenario-bound product metric. Compare it within the same prompt, settings, output cap, and provider path. Generation speed is the normalized sustained-output metric.

These are small-sample reports, usually one run per scenario. Treat them as a first pass, not a statistically stable benchmark.
