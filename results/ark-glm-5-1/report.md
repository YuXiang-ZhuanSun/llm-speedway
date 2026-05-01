# glm-5.1

`https://ark.cn-beijing.volces.com/api/coding/v3` | 1 run(s) per scenario | success 67%

## Read This First

Short chat starts in 24.56s. Long generation runs at 76.5 tok/s.

## Three Numbers

| Scenario | Round | First token | Task time | Output speed |
|---|---:|---:|---:|---:|
| long_generation | - | 44.76s | 73.55s | 76.5 tok/s |
| multi_turn | 1 | - | - | - |
| short_chat | - | 24.56s | 29.97s | 146.7 tok/s |

## How To Read

- First token: user-visible waiting time before the model starts speaking.
- Task time: end-to-end time for the fixed scenario prompt. Compare it within the same scenario.
- Output speed: generated tokens per second after the first token arrives.

## Errors

- `multi_turn` run `1` round `1`: [WinError 10054] 远程主机强迫关闭了一个现有的连接。
