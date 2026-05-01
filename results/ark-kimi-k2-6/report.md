# kimi-k2.6

`https://ark.cn-beijing.volces.com/api/coding/v3` | 1 run(s) per scenario | success 75%

## Read This First

Short chat starts in 13.04s. Long generation runs at 56.0 tok/s. Final multi-turn speed is 153.5 tok/s.

## Speed Metrics

| Scenario | Round | Start latency | Generation speed |
|---|---:|---:|---:|
| long_generation | - | 12.65s | 56.0 tok/s |
| multi_turn | 1 | 17.38s | 153.5 tok/s |
| multi_turn | 2 | - | - |
| short_chat | - | 13.04s | 333.5 tok/s |

## How To Read

- Start latency: user-visible waiting time before the model starts speaking.
- Generation speed: generated tokens per second after the first token arrives.
- Multi-turn speed: generation speed measured round by round while previous conversation history accumulates.
- total_latency_ms is still kept in raw_results.jsonl for debugging, but it is not a headline benchmark metric.

## Errors

- `multi_turn` run `1` round `2`: Empty visible assistant response.
