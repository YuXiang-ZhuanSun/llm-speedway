# deepseek-v4-flash

`https://api.deepseek.com` | 1 run(s) per scenario | success 100%

## Read This First

Short chat starts in 5.57s. Long generation runs at 96.0 tok/s. Final multi-turn speed is 59.3 tok/s.

## Speed Metrics

| Scenario | Round | Start latency | Generation speed |
|---|---:|---:|---:|
| long_generation | - | 6.75s | 96.0 tok/s |
| multi_turn | 1 | 4.42s | 73.0 tok/s |
| multi_turn | 2 | 5.58s | 116.3 tok/s |
| multi_turn | 3 | 8.21s | 258.3 tok/s |
| multi_turn | 4 | 6.23s | 101.1 tok/s |
| multi_turn | 5 | 8.27s | 59.3 tok/s |
| short_chat | - | 5.57s | 95.9 tok/s |

## How To Read

- Start latency: user-visible waiting time before the model starts speaking.
- Generation speed: generated tokens per second after the first token arrives.
- Multi-turn speed: generation speed measured round by round while previous conversation history accumulates.
- total_latency_ms is still kept in raw_results.jsonl for debugging, but it is not a headline benchmark metric.
