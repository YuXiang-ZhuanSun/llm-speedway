# doubao-seed-2.0-code

`https://ark.cn-beijing.volces.com/api/coding/v3` | 1 run(s) per scenario | success 100%

## Read This First

Short chat starts in 15.31s. Long generation runs at 105.1 tok/s. By the last multi-turn round, task time is 16.40s.

## Three Numbers

| Scenario | Round | First token | Task time | Output speed |
|---|---:|---:|---:|---:|
| long_generation | - | 27.77s | 46.86s | 105.1 tok/s |
| multi_turn | 1 | 18.37s | 28.50s | 111.9 tok/s |
| multi_turn | 2 | 73.02s | 79.28s | 162.1 tok/s |
| multi_turn | 3 | 15.72s | 25.83s | 93.0 tok/s |
| multi_turn | 4 | 11.00s | 23.42s | 58.0 tok/s |
| multi_turn | 5 | 5.95s | 16.40s | 57.7 tok/s |
| short_chat | - | 15.31s | 16.89s | 291.2 tok/s |

## How To Read

- First token: user-visible waiting time before the model starts speaking.
- Task time: end-to-end time for the fixed scenario prompt. Compare it within the same scenario.
- Output speed: generated tokens per second after the first token arrives.
