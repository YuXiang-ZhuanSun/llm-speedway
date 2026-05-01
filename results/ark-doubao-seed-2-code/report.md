# doubao-seed-2.0-code

`https://ark.cn-beijing.volces.com/api/coding/v3` | 1 run(s) per scenario | success 100%

## Read This First

Short chat starts in 15.31s. Long generation runs at 105.1 tok/s. Final multi-turn speed is 57.7 tok/s.

## Speed Metrics

| Scenario | Round | Start latency | Generation speed |
|---|---:|---:|---:|
| long_generation | - | 27.77s | 105.1 tok/s |
| multi_turn | 1 | 18.37s | 111.9 tok/s |
| multi_turn | 2 | 73.02s | 162.1 tok/s |
| multi_turn | 3 | 15.72s | 93.0 tok/s |
| multi_turn | 4 | 11.00s | 58.0 tok/s |
| multi_turn | 5 | 5.95s | 57.7 tok/s |
| short_chat | - | 15.31s | 291.2 tok/s |

## How To Read

- Start latency: user-visible waiting time before the model starts speaking.
- Generation speed: generated tokens per second after the first token arrives.
- Multi-turn speed: generation speed measured round by round while previous conversation history accumulates.
- total_latency_ms is still kept in raw_results.jsonl for debugging, but it is not a headline benchmark metric.
