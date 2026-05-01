<p align="center">
  <img src="assets/logo.svg" alt="llm-speedway logo" width="560">
</p>

# llm-speedway

**Find the LLM API that makes agents feel fast: first token, task time, and output speed in one clean report.**

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

`llm-speedway` benchmarks the part users actually feel. It measures when the first token appears, how long a controlled task takes, and how fast the model writes once it starts. The output is not a spreadsheet wall. It is a report you can read before choosing a model for an agent, coding assistant, chat product, or automation workflow.

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

## The three numbers

| Metric | Meaning | Why it matters |
|---|---|---|
| **First token** | Time until the first visible assistant token arrives | The user stops staring at an empty screen |
| **Task time** | End-to-end time for the fixed scenario prompt | The product workflow is done |
| **Output speed** | Tokens per second after the first token | The model's sustained generation pace |

### About "Task time"

Task time is not a universal model speed score. Response length can vary.

`llm-speedway` treats it as a **scenario-level product metric**: compare it within the same prompt, same model settings, same output cap, and same provider path. For normalized generation speed, use **Output speed**. For perceived responsiveness, use **First token**.

That distinction is the point. Agent UX is not one number.

## Scenarios

The built-in suite is small because each scenario maps to a real agent pain.

| Scenario | What it tests |
|---|---|
| `short_chat` | Lightweight chat responsiveness: "does it start fast?" |
| `long_generation` | Sustained generation: "does it keep writing quickly?" |
| `multi_turn` | Growing context: "what happens after the conversation gets heavier?" |

These three cover the common failure mode in agents: slow start, slow writing, and degraded multi-turn behavior.

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

| Model | First token, short chat | Output speed, long generation | Multi-turn |
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
| 4. Measure | `core/metrics.py` | Convert stream events into first token, task time, output speed |
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

The report promotes only:

- `ttft_ms` -> First token
- `total_latency_ms` -> Task time
- `decode_tps` -> Output speed

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
