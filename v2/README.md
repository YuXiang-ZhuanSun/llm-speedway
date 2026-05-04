<p align="center">
  <img src="../v1/assets/logo.svg" alt="llm-speedway logo" width="560">
</p>

# llm-speedway V2

**Find the LLM API that makes agents fast: start latency, generation speed, and multi-turn speed.**

V2 is the desktop app version of `llm-speedway`, built with Tauri, React, TypeScript, Rust, and SQLite.

Agents are slow in a very specific way: they often make you wait in silence.

When an agent is working, a slow API turns into human waiting time. `llm-speedway` helps compare whether an API is fast and stable across the signals that matter for agent work: start latency, generation speed, and multi-turn speed.

It runs locally, stores provider configs and benchmark history locally, and sends requests only to the API endpoint you configure.

## Install

### From GitHub Releases

Download the latest installer from [GitHub Releases](https://github.com/YuXiang-ZhuanSun/llm-speedway/releases).

| Platform | File | How to use |
|---|---|---|
| Windows | `.msi` or `.exe` | Install and launch |
| macOS | `.dmg` | Open the DMG |
| Linux | `.AppImage` or `.deb` | Run the AppImage or install the deb |

If a release has no files yet, install from source.

### From Source

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

Build local installers:

```bash
npm run desktop:build
```

Generated packages are written under `src-tauri/target/**/release/bundle/`.

## Development

Frontend production build:

```bash
npm run build
```

Desktop development build:

```bash
npm run desktop:dev
```

Rust validation:

```bash
cd src-tauri
cargo check
```

## Release

The release workflow is at:

```text
../.github/workflows/desktop-release.yml
```

Publishing a `v*` tag, or manually running the workflow with a release tag, builds and uploads:

- Windows: MSI and NSIS EXE
- macOS: DMG
- Linux: AppImage and deb package

The workflow also checks that bundle files exist before the job succeeds. A platform job that produces no installer fails instead of leaving an empty release behind.

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

Local data:

```text
~/.llm-speedway/llm-speedway.db
```

Important directories:

```text
src/                    # React + TypeScript UI
src-tauri/src/commands/ # Tauri command API
src-tauri/src/services/ # Provider and speedtest services
src-tauri/src/database/ # SQLite setup and access
docs/                   # Product and release notes
```

## V1

The original CLI version is still available in [`../v1`](../v1).
