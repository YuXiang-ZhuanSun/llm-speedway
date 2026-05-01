# llm-speedway Public Benchmark Reports

All runs use the same three visible metrics:

- First token
- Task time
- Output speed

| Model | Short chat first token | Long generation speed | Multi-turn status | Report |
|---|---:|---:|---|---|
| `deepseek-v4-flash` | 6.33s | 97.6 tok/s | success | [report](deepseek-v4-flash/report.md) |
| `doubao-seed-2.0-code` | 15.31s | 105.1 tok/s | success | [report](ark-doubao-seed-2-code/report.md) |
| `glm-5.1` | 24.56s | 76.5 tok/s | failed on round 1 | [report](ark-glm-5-1/report.md) |
| `kimi-k2.6` | 11.88s | 68.3 tok/s | empty visible response on round 1 | [report](ark-kimi-k2-6/report.md) |

Task time is a scenario-level product metric. Compare it within the same prompt and settings. Output speed is the normalized generation metric.

These are small-sample reports, usually one run per scenario. Treat them as a first pass, not a statistically stable benchmark.
