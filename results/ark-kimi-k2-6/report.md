# kimi-k2.6

`https://ark.cn-beijing.volces.com/api/coding/v3` | 1 run(s) per scenario | success 67%

## Read This First

Short chat starts in 11.88s. Long generation runs at 68.3 tok/s.

## Request Metrics

| Scenario | Round | Start latency | Completion time | Generation speed |
|---|---:|---:|---:|---:|
| long_generation | - | 12.67s | 27.65s | 68.3 tok/s |
| multi_turn | 1 | - | - | - |
| short_chat | - | 11.88s | 11.94s | 4110.1 tok/s |

## How To Read

- Start latency: user-visible waiting time before the model starts speaking.
- Generation speed: generated tokens per second after the first token arrives.
- Completion time: end-to-end time for the fixed scenario or round. Compare it only within the same prompt and settings.
- multi_turn: a sequence of requests carrying previous conversation history, used to expose context-growth slowdown.

## Errors

- `multi_turn` run `1` round `1`: Empty visible assistant response.
