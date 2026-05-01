# glm-5.1

`https://ark.cn-beijing.volces.com/api/coding/v3` | 1 run(s) per scenario | success 67%

## Read This First

Short chat starts in 24.56s. Long generation runs at 76.5 tok/s.

## Request Metrics

| Scenario | Round | Start latency | Completion time | Generation speed |
|---|---:|---:|---:|---:|
| long_generation | - | 44.76s | 73.55s | 76.5 tok/s |
| multi_turn | 1 | - | - | - |
| short_chat | - | 24.56s | 29.97s | 146.7 tok/s |

## How To Read

- Start latency: user-visible waiting time before the model starts speaking.
- Generation speed: generated tokens per second after the first token arrives.
- Completion time: end-to-end time for the fixed scenario or round. Compare it only within the same prompt and settings.
- multi_turn: a sequence of requests carrying previous conversation history, used to expose context-growth slowdown.

## Errors

- `multi_turn` run `1` round `1`: [WinError 10054] 远程主机强迫关闭了一个现有的连接。
