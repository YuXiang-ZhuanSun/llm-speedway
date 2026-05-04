# glm-5.1

`https://ark.cn-beijing.volces.com/api/coding/v3` | 1 run(s) per scenario | success 100%

## Read This First

Short chat starts in 28.71s. Long generation runs at 67.4 tok/s. Final multi-turn speed is 64.5 tok/s.

## Speed Metrics

| Scenario | Round | Start latency | Generation speed |
|---|---:|---:|---:|
| long_generation | - | 53.57s | 67.4 tok/s |
| multi_turn | 1 | 33.37s | 86.2 tok/s |
| multi_turn | 2 | 40.38s | 76.5 tok/s |
| multi_turn | 3 | 40.62s | 101.3 tok/s |
| multi_turn | 4 | 64.21s | 29.3 tok/s |
| multi_turn | 5 | 47.23s | 64.5 tok/s |
| short_chat | - | 28.71s | 501.8 tok/s |

## How To Read

- Start latency: user-visible waiting time before the model starts speaking.
- Generation speed: generated tokens per second after the first token arrives.
- Multi-turn speed: generation speed measured round by round while previous conversation history accumulates.
- Extra timing fields such as total_latency_ms are kept in raw_results.jsonl for debugging.
