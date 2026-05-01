<p align="center">
  <img src="assets/logo.svg" alt="llm-speedway logo" width="560">
</p>

# llm-speedway

**Find the LLM API that makes agents feel fast: start latency, generation speed, and multi-turn speed in one clean report.**

<p>
  <a href="README.zh-CN.md">中文</a>
  |
  <a href="results/README.md">Benchmarks</a>
  |
  <a href="configs">Configs</a>
</p>

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![OpenAI Compatible](https://img.shields.io/badge/API-OpenAI--compatible-111827)
![Streaming](https://img.shields.io/badge/Streaming-TTFT-2563EB)
![Reports](https://img.shields.io/badge/Reports-Markdown%20%2B%20CSV-0F766E)
![Local CLI](https://img.shields.io/badge/Run-Local%20CLI-475569)

Agents are slow in a very specific way: they often make you wait in silence.

`llm-speedway` benchmarks the part users actually feel. It measures when the first token appears, how fast the model writes once it starts, and whether that speed survives accumulated conversation context. The output is not a spreadsheet wall. It is a report you can read before choosing a model for an agent, coding assistant, chat product, or automation workflow.

## What it is

`llm-speedway` is a local benchmark runner for OpenAI-compatible Chat Completions APIs.

It sends controlled prompts, listens to streaming responses, captures first-token timing, validates that visible assistant text was actually produced, and writes:

```text
results/<model>/
  report.md          # human report
  summary.csv        # three headline metrics
  raw_results.jsonl  # full request-level data
```

Nothing is sent anywhere except the API endpoint you configure.

## Evaluation model

`llm-speedway` separates **raw fields** from **headline metrics**. Raw records keep timing details for debugging. The benchmark itself promotes three speed signals.

| Metric | Source | Meaning | Use it for |
|---|---|---|---|
| **Start latency** | `ttft_ms` | Time until the first visible assistant token arrives | Whether the agent starts talking fast |
| **Generation speed** | `long_generation.decode_tps` | Tokens per second after the first token on a long answer | Whether the model keeps writing quickly |
| **Multi-turn speed** | `multi_turn.decode_tps` by round | Generation speed while conversation history accumulates | Whether the model stays fast as context grows |

### About completion time

`total_latency_ms` is still recorded for every request, but it is not a headline benchmark metric.

Completion time changes with answer length, stopping behavior, and provider-side truncation. It is useful for debugging a specific run, but it is too ambiguous to headline as a cross-model speed signal. For sustained output, use **Generation speed**. For context-heavy agents, use **Multi-turn speed**.

That distinction is the point. Agent UX is not one number.

## Scenarios

The built-in suite is small because each scenario maps to a real agent pain.

| Scenario | What it tests | How to read it |
|---|---|---|
| `short_chat` | Lightweight chat responsiveness | Look mainly at start latency |
| `long_generation` | Sustained generation | Look mainly at generation speed |
| `multi_turn` | Context accumulation | Compare each round as history grows |

These three cover the common failure mode in agents: slow start, slow writing, and degraded multi-turn speed.

`multi_turn` is not "one multi-round answer." It is a sequence of requests. Round 2 carries round 1's assistant reply; round 3 carries the previous two rounds, and so on. This shows whether the same model gets slower as the conversation context becomes heavier.

## Install

Install locally:

```powershell
pip install -e .
```

Or run the test suite directly:

```powershell
python -m unittest discover -s tests
```

No SDK is required. The OpenAI-compatible adapter uses the Python standard library.

## Quickstart

Create a config:

```powershell
Copy-Item configs/config.example.json config.json
```

Use an environment variable for the API key:

```json
{
  "api": {
    "base_url": "https://api.example.com/v1",
    "api_key_env": "LLM_API_KEY",
    "model": "model-name"
  }
}
```

Run:

```powershell
llm-speedway run --config config.json
```

Run a single scenario:

```powershell
llm-speedway run --config config.json --scenario short_chat --runs 3
```

## Benchmarks

Committed small-sample reports live in [results](results/README.md).

| Model | Start latency | Generation speed | Multi-turn speed |
|---|---:|---:|---|
| `deepseek-v4-flash` | 6.33s | 97.6 tok/s | success |
| `doubao-seed-2.0-code` | 15.31s | 105.1 tok/s | success |
| `glm-5.1` | 24.56s | 76.5 tok/s | failed on round 1 |
| `kimi-k2.6` | 11.88s | 68.3 tok/s | empty visible response on round 1 |

These are first-pass reports, not statistical claims. Increase `runs_per_scenario` when you need confidence intervals instead of a quick model screen.

## Architecture

`llm-speedway` has one pipeline: **define the run, call the model, measure the stream, write the report.**

| Stage | Module | Job |
|---|---|---|
| 1. Define | `configs/` + root `scenarios/` | Choose model, endpoint, runs, and prompt shape |
| 2. Run | `runner.py` | Execute each scenario and preserve request-level records |
| 3. Call | `providers/` | Talk to OpenAI-compatible streaming APIs |
| 4. Measure | `core/metrics.py` | Convert stream events into start latency and generation speed |
| 5. Report | `reports/` + `results/` | Produce Markdown, CSV, and JSONL artifacts |

```text
config + scenario
      |
      v
runner -> provider -> LLM API -> stream events
      |                              |
      v                              v
raw records --------------------> metrics
                                     |
                                     v
                         report.md / summary.csv / raw_results.jsonl
```

The code layout follows the same boundaries:

```text
llm_speedway/
  cli.py                  # command entry
  runner.py               # benchmark orchestration
  core/                   # config, metrics, token estimation
  providers/              # API protocol adapters
  scenarios/              # scenario JSON loader
  reports/                # Markdown / CSV / JSONL writers
configs/                  # reusable provider configs
scenarios/                # extensible benchmark cases
tests/                    # metric and summary tests
results/                  # committed benchmark reports
assets/                   # logo and README assets
```

Why this shape:

| Layer | Responsibility |
|---|---|
| `core/` | Config parsing, metric math, token estimation |
| `providers/` | API protocol adapters; currently OpenAI-compatible Chat API |
| `llm_speedway/scenarios/` | Scenario JSON loading and validation |
| `reports/` | Markdown and CSV output |
| `runner.py` | Orchestration across provider, scenario, metrics, and report |

Adding a provider should not touch metrics. Adding a scenario should not touch HTTP. Changing the report should not rewrite raw data.

## Extending scenarios

Benchmark cases live outside the Python package:

```text
scenarios/
  short_chat.json
  long_generation.json
  multi_turn.json
```

Add a new JSON file:

```json
{
  "name": "agent_tool_call",
  "description": "Tool-heavy agent task.",
  "kind": "single_turn",
  "max_tokens": 512,
  "prompts": [
    "Plan a three-step refactor for a Python CLI project."
  ]
}
```

Then reference it in config:

```json
{
  "benchmark": {
    "scenarios_dir": "scenarios"
  },
  "scenarios": ["agent_tool_call"]
}
```

## Data model

Each request produces one raw record:

```json
{
  "scenario": "short_chat",
  "model": "deepseek-v4-flash",
  "success": true,
  "ttft_ms": 6330.12,
  "total_latency_ms": 7050.44,
  "decode_tps": 219.8,
  "finish_reason": "stop"
}
```

The report promotes:

- `ttft_ms` -> Start latency
- `long_generation.decode_tps` -> Generation speed
- `multi_turn.decode_tps` -> Multi-turn speed

`total_latency_ms` remains in raw records for debugging and reproducibility, but it is not one of the headline benchmark metrics.

If a streamed response contains no visible assistant content, the sample fails. Empty answers do not get pretty numbers.

## Roadmap

- Anthropic-compatible provider adapter
- Concurrent agent-load mode
- Provider-specific streaming normalization
- External scenario files
- HTML report export

## Principle

Fast token matters.

If an agent is going to take time, it should at least start talking.
