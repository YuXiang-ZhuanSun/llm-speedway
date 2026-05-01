# deepseek-v4-flash

`https://api.deepseek.com` | 1 run(s) per scenario | success 100%

## Read This First

Short chat starts in 6.33s. Long generation runs at 97.6 tok/s. By the last multi-turn round, task time is 9.48s.

## Three Numbers

| Scenario | Round | First token | Task time | Output speed |
|---|---:|---:|---:|---:|
| long_generation | - | 5.98s | 16.47s | 97.6 tok/s |
| multi_turn | 1 | 6.43s | 11.42s | 102.4 tok/s |
| multi_turn | 2 | 6.34s | 9.62s | 155.8 tok/s |
| multi_turn | 3 | 8.18s | 12.72s | 112.8 tok/s |
| multi_turn | 4 | 6.52s | 9.27s | 186.0 tok/s |
| multi_turn | 5 | 4.81s | 9.48s | 109.6 tok/s |
| short_chat | - | 6.33s | 7.05s | 219.8 tok/s |

## How To Read

- First token: user-visible waiting time before the model starts speaking.
- Task time: end-to-end time for the fixed scenario prompt. Compare it within the same scenario.
- Output speed: generated tokens per second after the first token arrives.
