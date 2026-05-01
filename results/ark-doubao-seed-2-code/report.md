# doubao-seed-2.0-code

`https://ark.cn-beijing.volces.com/api/coding/v3` | 1 run(s) per scenario | success 100%

## Read This First

Short chat starts in 13.32s. Long generation runs at 103.2 tok/s. Final multi-turn speed is 92.4 tok/s.

## Speed Metrics

| Scenario | Round | Start latency | Generation speed |
|---|---:|---:|---:|
| long_generation | - | 26.57s | 103.2 tok/s |
| multi_turn | 1 | 25.95s | 129.2 tok/s |
| multi_turn | 2 | 21.44s | 112.5 tok/s |
| multi_turn | 3 | 44.95s | 205.6 tok/s |
| multi_turn | 4 | 30.08s | 188.3 tok/s |
| multi_turn | 5 | 22.64s | 92.4 tok/s |
| short_chat | - | 13.32s | 95.6 tok/s |

## How To Read

- Start latency: user-visible waiting time before the model starts speaking.
- Generation speed: generated tokens per second after the first token arrives.
- Multi-turn speed: generation speed measured round by round while previous conversation history accumulates.
- Extra timing fields such as total_latency_ms are kept in raw_results.jsonl for debugging.
