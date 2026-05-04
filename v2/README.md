<p align="center">
  <img src="../v1/assets/logo.svg" alt="llm-speedway logo" width="560">
</p>

# llm-speedway V2

**一个跨平台桌面端 LLM API 测速工具：集中管理 API key、模型、API 地址，一键测速，并用可比较的结果帮你选择更快的 Agent API。**

<p>
  <a href="../v1/README.md">V1 CLI</a>
  |
  <a href="docs/prd-v2-cross-platform.zh-CN.md">V2 PRD</a>
  |
  <a href="../v1/results/README.md">V1 Benchmarks</a>
</p>

![Tauri](https://img.shields.io/badge/Desktop-Tauri-24C8DB)
![React](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-2563EB)
![Rust](https://img.shields.io/badge/Backend-Rust-B7410E)
![SQLite](https://img.shields.io/badge/Storage-SQLite-0F766E)
![OpenAI Compatible](https://img.shields.io/badge/API-OpenAI--compatible-111827)

V1 解决的是“命令行里怎么测”。V2 解决的是“日常怎么用”：用户可以不断添加不同供应商、不同模型、不同 API 地址和不同 key，点击测速后看到等待窗口，测速完成后得到可排序、可比较、可导出的结果。

## What It Is

`llm-speedway V2` 是一个本地运行的跨平台桌面应用，面向 OpenAI-compatible Chat Completions API。

它会提供：

- API 配置管理：供应商、模型、base URL、endpoint、API key、标签、备注。
- 一键测速：对单个配置或多个配置发起测速。
- 等待窗口：展示连接检查、短对话、长生成、多轮测试、汇总保存等阶段。
- 结果表格：展示首 token 延迟、生成速度、多轮速度、状态和测试时间。
- 历史记录：保存每次测速结果，便于复测和对比。
- 导出能力：导出 Markdown、CSV、JSONL，兼容 V1 的报告思路。

默认情况下，除了用户配置的 LLM API endpoint，应用不会把 API key、prompt 或结果发送到其他地方。

## Speed Signals

V2 继续沿用 V1 的三个核心速度信号。

| Signal | Field | Meaning | Use it for |
|---|---|---|---|
| **Start latency** | `ttft_ms` | 第一段可见 assistant 内容到达时间 | 判断 Agent 是否很快开始响应 |
| **Generation speed** | `decode_tps` | 首 token 后的 tokens/s | 判断模型持续输出是否足够快 |
| **Multi-turn speed** | `multi_turn_decode_tps` | 上下文累积后的 tokens/s | 判断多轮对话变重后是否仍然稳定 |

额外字段如 `total_latency_ms`、`success_rate`、`error_message` 会保留用于排查问题和比较稳定性。

## Product Flow

```text
添加 API 配置
      |
      v
选择单个或多个配置
      |
      v
点击测速 -> 等待窗口显示阶段进度
      |
      v
结果写入本地 SQLite
      |
      v
查看详情 / 排序比较 / 导出报告
```

## Architecture

V2 参考 cc-Switch 的分层架构。

```text
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + TS)                    │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ Components  │  │    Hooks     │  │  TanStack Query  │    │
│  │     UI      │──│ Business UI  │──│  Cache / Sync    │    │
│  └─────────────┘  └──────────────┘  └──────────────────┘    │
└────────────────────────┬────────────────────────────────────┘
                         │ Tauri IPC
┌────────────────────────▼────────────────────────────────────┐
│                   Backend (Tauri + Rust)                    │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │  Commands   │  │   Services   │  │  Models / DAO    │    │
│  │   API       │──│  Business    │──│  Data / Config   │    │
│  └─────────────┘  └──────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

Core design:

- SSOT：可同步业务数据存储在 `~/.llm-speedway/llm-speedway.db`。
- 双层存储：SQLite 保存配置、测速任务、历史结果；JSON 保存设备级设置。
- 原子写入：导出、备份和 JSON 设置使用临时文件 + 重命名。
- 并发安全：数据库连接由 Rust 后端统一保护。
- 分层架构：Commands -> Services -> DAO -> Database。

## Current Skeleton

```text
v2/
  src/                    # React + TypeScript frontend
  src-tauri/              # Tauri + Rust backend
  docs/                   # V2 PRD and product docs
  package.json
  vite.config.ts
```

当前骨架已经按发布型桌面应用组织：前端通过 Tauri IPC 调用 Rust commands，Rust 后端按 Commands -> Services -> Database 分层，并将配置和测速结果写入本地 SQLite。浏览器模式仅用于 UI 预览，不代表最终运行形态。

## Development

Install dependencies:

```powershell
cd v2
npm install
```

Run the frontend only:

```powershell
npm run dev
```

Run as a Tauri desktop app after installing Rust and platform prerequisites:

```powershell
npm run desktop:dev
```

Build release packages:

```powershell
npm run desktop:build
```

Tauri 官方推荐使用 `create-tauri-app` 创建 React/TypeScript 模板；当前仓库按同类结构手动放好初始骨架，并补齐了发布工作流。

## Release

V2 不是前后端分离部署项目。最终发布方式是 Tauri 桌面安装包：

- Windows: `.msi` / portable package
- macOS: `.dmg` / `.app.tar.gz`
- Linux: `.deb` / `.rpm` / `.AppImage`

GitHub Actions workflow lives at:

```text
../.github/workflows/desktop-release.yml
```

Push a `v*` tag or manually run the workflow to create a draft release with platform artifacts.

See [`docs/release-architecture.zh-CN.md`](docs/release-architecture.zh-CN.md).

## MVP Scope

- Tauri + React + TypeScript project skeleton.
- API 配置 CRUD。
- 单个配置测速。
- 等待弹窗和取消按钮。
- 结果表格和结果详情。
- Markdown、CSV 导出。
- Windows、macOS、Linux 构建配置。

## V1

第一版 CLI 已移动到 [`../v1`](../v1)。它仍然是完整的 Python 项目，可以继续用：

```powershell
cd v1
pip install -e .
llm-speedway run --config config.json
```
