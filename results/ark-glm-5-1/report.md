# glm-5.1

`https://ark.cn-beijing.volces.com/api/coding/v3` | 1 run(s) per scenario | success 67%

## Read This First

Short chat starts in 24.56s. Long generation runs at 76.5 tok/s.

## Speed Metrics

| Scenario | Round | Start latency | Generation speed |
|---|---:|---:|---:|
| long_generation | - | 44.76s | 76.5 tok/s |
| multi_turn | 1 | - | - |
| short_chat | - | 24.56s | 146.7 tok/s |

## How To Read

- Start latency: user-visible waiting time before the model starts speaking.
- Generation speed: generated tokens per second after the first token arrives.
- Multi-turn speed: generation speed measured round by round while previous conversation history accumulates.
- total_latency_ms is still kept in raw_results.jsonl for debugging, but it is not a headline benchmark metric.

## Errors

- `multi_turn` run `1` round `1`: [WinError 10054] 远程主机强迫关闭了一个现有的连接。
