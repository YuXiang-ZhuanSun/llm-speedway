# llm-speedway Public Benchmark Reports

All public reports use the same three benchmark signals:

- Start latency: `short_chat.ttft_ms`, time until the first visible assistant token.
- Generation speed: `long_generation.decode_tps`, sustained tokens/s on a long answer.
- Multi-turn speed: `multi_turn.decode_tps` by round, measured as conversation history accumulates.

Extra timing fields such as `total_latency_ms` remain available in raw JSONL files for debugging.

| Model | Start latency | Generation speed | Multi-turn speed | Report |
|---|---:|---:|---|---|
| `deepseek-v4-flash` | 5.57s | 96.0 tok/s | final round 59.3 tok/s | [report](deepseek-v4-flash/report.md) |
| `doubao-seed-2.0-code` | 13.32s | 103.2 tok/s | final round 92.4 tok/s | [report](ark-doubao-seed-2-code/report.md) |
| `glm-5.1` | 28.71s | 67.4 tok/s | final round 64.5 tok/s | [report](ark-glm-5-1/report.md) |
| `kimi-k2.6` | 13.04s | 56.0 tok/s | round 1 153.5 tok/s, failed on round 2 | [report](ark-kimi-k2-6/report.md) |

`multi_turn` is a context-accumulation test: each round is a new request that carries previous conversation history.

These are small-sample reports, usually one run per scenario. Treat them as a first pass, not a statistically stable benchmark.
