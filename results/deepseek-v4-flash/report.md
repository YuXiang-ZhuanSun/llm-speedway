# deepseek-v4-flash

`https://api.deepseek.com` | 1 run(s) per scenario | success 100%

## Read This First

Short chat starts in 6.33s. Long generation runs at 97.6 tok/s. Final multi-turn speed is 109.6 tok/s.

## Speed Metrics

| Scenario | Round | Start latency | Generation speed |
|---|---:|---:|---:|
| long_generation | - | 5.98s | 97.6 tok/s |
| multi_turn | 1 | 6.43s | 102.4 tok/s |
| multi_turn | 2 | 6.34s | 155.8 tok/s |
| multi_turn | 3 | 8.18s | 112.8 tok/s |
| multi_turn | 4 | 6.52s | 186.0 tok/s |
| multi_turn | 5 | 4.81s | 109.6 tok/s |
| short_chat | - | 6.33s | 219.8 tok/s |

## How To Read

- Start latency: user-visible waiting time before the model starts speaking.
- Generation speed: generated tokens per second after the first token arrives.
- Multi-turn speed: generation speed measured round by round while previous conversation history accumulates.
- total_latency_ms is still kept in raw_results.jsonl for debugging, but it is not a headline benchmark metric.
