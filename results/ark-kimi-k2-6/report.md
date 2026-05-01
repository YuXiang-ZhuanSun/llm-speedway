# kimi-k2.6

`https://ark.cn-beijing.volces.com/api/coding/v3` | 1 run(s) per scenario | success 67%

## Read This First

Short chat starts in 11.88s. Long generation runs at 68.3 tok/s.

## Three Numbers

| Scenario | Round | First token | Task time | Output speed |
|---|---:|---:|---:|---:|
| long_generation | - | 12.67s | 27.65s | 68.3 tok/s |
| multi_turn | 1 | - | - | - |
| short_chat | - | 11.88s | 11.94s | 4110.1 tok/s |

## How To Read

- First token: user-visible waiting time before the model starts speaking.
- Task time: end-to-end time for the fixed scenario prompt. Compare it within the same scenario.
- Output speed: generated tokens per second after the first token arrives.

## Errors

- `multi_turn` run `1` round `1`: Empty visible assistant response.
