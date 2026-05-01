# deepseek-v4-flash

`https://api.deepseek.com` | 1 run(s) per scenario | success 100%

## Read This First

Short chat starts in 6.33s. Long generation runs at 97.6 tok/s. By the last multi-turn round, completion time is 9.48s.

## Request Metrics

| Scenario | Round | Start latency | Completion time | Generation speed |
|---|---:|---:|---:|---:|
| long_generation | - | 5.98s | 16.47s | 97.6 tok/s |
| multi_turn | 1 | 6.43s | 11.42s | 102.4 tok/s |
| multi_turn | 2 | 6.34s | 9.62s | 155.8 tok/s |
| multi_turn | 3 | 8.18s | 12.72s | 112.8 tok/s |
| multi_turn | 4 | 6.52s | 9.27s | 186.0 tok/s |
| multi_turn | 5 | 4.81s | 9.48s | 109.6 tok/s |
| short_chat | - | 6.33s | 7.05s | 219.8 tok/s |

## How To Read

- Start latency: user-visible waiting time before the model starts speaking.
- Generation speed: generated tokens per second after the first token arrives.
- Completion time: end-to-end time for the fixed scenario or round. Compare it only within the same prompt and settings.
- multi_turn: a sequence of requests carrying previous conversation history, used to expose context-growth slowdown.
