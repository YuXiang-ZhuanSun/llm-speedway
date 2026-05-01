# llm-speedway Public Benchmark Reports

All public reports use the same three benchmark signals:

- Start latency: `short_chat.ttft_ms`, time until the first visible assistant token.
- Generation speed: `long_generation.decode_tps`, sustained tokens/s on a long answer.
- Multi-turn speed: `multi_turn.decode_tps` by round, measured as conversation history accumulates.

`total_latency_ms` is still available in raw JSONL files for debugging, but it is not a headline benchmark metric.

| Model | Start latency | Generation speed | Multi-turn speed | Report |
|---|---:|---:|---|---|
| `deepseek-v4-flash` | 6.33s | 97.6 tok/s | final round 109.6 tok/s | [report](deepseek-v4-flash/report.md) |
| `doubao-seed-2.0-code` | 15.31s | 105.1 tok/s | final round 57.7 tok/s | [report](ark-doubao-seed-2-code/report.md) |
| `glm-5.1` | 24.56s | 76.5 tok/s | failed on round 1 | [report](ark-glm-5-1/report.md) |
| `kimi-k2.6` | 11.88s | 68.3 tok/s | empty visible response on round 1 | [report](ark-kimi-k2-6/report.md) |

`multi_turn` is a context-accumulation test: each round is a new request that carries previous conversation history.

These are small-sample reports, usually one run per scenario. Treat them as a first pass, not a statistically stable benchmark.
