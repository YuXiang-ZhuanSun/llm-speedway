<p align="center">
  <img src="v1/assets/logo.svg" alt="llm-speedway logo" width="560">
</p>

# llm-speedway

**Find the LLM API that makes agents fast: start latency, generation speed, and multi-turn speed.**

<p>
  <a href="README.zh-CN.md">中文</a>
  |
  <a href="v1/results/README.md">Benchmarks</a>
  |
  <a href="v1/docs/source-walkthrough.zh-CN.md">Source Walkthrough</a>
  |
  <a href="v1/configs">V1 Configs</a>
  |
  <a href="v2/docs/prd-v2-cross-platform.zh-CN.md">V2 PRD</a>
</p>

![Desktop](https://img.shields.io/badge/Desktop-Tauri-9A4F18)
![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-111827)
![Backend](https://img.shields.io/badge/Backend-Rust-7C2D12)
![Storage](https://img.shields.io/badge/Storage-SQLite-475569)
![API](https://img.shields.io/badge/API-OpenAI%20%2B%20Anthropic-111827)
![Reports](https://img.shields.io/badge/Signals-TTFT%20%2B%20TPS-9A4F18)

Agents are slow in a very specific way: they often make you wait in silence.

When an agent is working, a slow API turns into human waiting time. That is frustrating, and it compounds across every tool call, retry, and multi-turn task. `llm-speedway` helps you find APIs that are not just fast once, but fast and stable where agent UX actually breaks: start latency, generation speed, and multi-turn speed.

V2 is a Tauri desktop app. Add provider configs, run speed tests, and compare results locally.

![llm-speedway desktop screenshot](v2/assets/screenshot.png)

## Install

### Recommended: GitHub Releases

Download the latest installer from [GitHub Releases](https://github.com/YuXiang-ZhuanSun/llm-speedway/releases).

Expected assets:

| Platform | File | How to use |
|---|---|---|
| Windows | `.msi` or `.exe` | Install and launch `llm-speedway` |
| macOS | `.dmg` | Open the DMG, then launch the app |
| Linux | `.AppImage` or `.deb` | Run the AppImage or install the deb package |

If the release page has no files for your platform yet, use the source install below.

### Source Install

Prerequisites:

- Node.js 20+
- Rust stable
- Tauri system dependencies for your platform

Windows also needs Visual Studio Build Tools with the C++ workload.

```bash
git clone https://github.com/YuXiang-ZhuanSun/llm-speedway.git
cd llm-speedway/v2
npm ci
npm run desktop:dev
```

Build a local desktop package:

```bash
npm run desktop:build
```

The generated installers are written under `v2/src-tauri/target/**/release/bundle/`.

## Quickstart

1. Open `llm-speedway`.
2. Click **Add config**.
3. Fill in provider name, base URL, model, API key, and API format.
4. Choose `OpenAI compatible` or `Anthropic compatible`.
5. Click **Speedtest**.
6. Compare start latency, generation speed, multi-turn speed, and success rate.

Bad keys, wrong models, fake APIs, and incorrect endpoints fail as real failures. The app does not fabricate benchmark numbers.

## What It Measures

| Signal | Field | Meaning |
|---|---|---|
| Start latency | `ttft_ms` | Time until the first visible assistant token arrives |
| Generation speed | `decode_tps` | Estimated tokens per second after the first token |
| Multi-turn speed | `multi_turn_decode_tps` | Generation speed after conversation history has accumulated |

## API Formats

OpenAI-compatible APIs use:

```text
POST /chat/completions
Authorization: Bearer <API_KEY>
```

Anthropic-compatible APIs use:

```text
POST /v1/messages
x-api-key: <API_KEY>
anthropic-version: 2023-06-01
```

## Architecture

```text
React + TypeScript UI
        |
        | Tauri IPC
        v
Rust commands
        |
        v
Services -> SQLite -> Speedtest HTTP streaming
```

Local data is stored at:

```text
~/.llm-speedway/llm-speedway.db
```

Project layout:

```text
v1/        # Original Python CLI benchmark runner
v2/        # Tauri + React + Rust desktop app
```

## Release Builds

Desktop releases are built by `.github/workflows/desktop-release.yml`.

Publishing a `v*` tag, or manually running the workflow with a release tag, builds:

- Windows: MSI and NSIS EXE
- macOS: DMG
- Linux: AppImage and deb package

The workflow fails if a platform build finishes without producing installer files, so an empty release should not be published silently.

## Development

```bash
cd v2
npm ci
npm run build
npm run desktop:dev
```

Rust validation:

```bash
cd v2/src-tauri
cargo check
```

## V1

The first version is preserved in [`v1/`](v1/). It remains a Python CLI benchmark runner with Markdown, CSV, and JSONL output.

## License

MIT
