<p align="center">
  <img src="v1/assets/logo.svg" alt="llm-speedway logo" width="560">
</p>

# llm-speedway

**Find the LLM API that makes agents fast: start latency, generation speed, and multi-turn speed.**

<p>
  <a href="README.md">English</a>
  |
  <a href="v1/results/README.md">Benchmarks</a>
  |
  <a href="v1/docs/source-walkthrough.zh-CN.md">源码导读</a>
  |
  <a href="v1/configs">V1 配置</a>
  |
  <a href="v2/docs/prd-v2-cross-platform.zh-CN.md">V2 PRD</a>
</p>

Agents are slow in a very specific way: they often make you wait in silence.

Agent 干活的时候，API 一慢，人类就只能在屏幕前等。这很让人不爽，而且每一次工具调用、重试、多轮任务都会把这种等待放大。`llm-speedway` 要清晰测出 API 是不是又快又稳：首 token 延迟够不够低、持续生成够不够快、多轮上下文变重之后还能不能保持速度。

V2 是一个 Tauri 桌面应用。你可以添加不同供应商、模型、base URL 和 API key，运行测评，并在本地对比结果。

![llm-speedway desktop screenshot](v2/assets/screenshot.png)

## 安装

### 推荐方式：从 GitHub Releases 下载

打开 [GitHub Releases](https://github.com/YuXiang-ZhuanSun/llm-speedway/releases)，下载适合你系统的安装包。

应该发布的文件：

| 平台 | 文件 | 使用方式 |
|---|---|---|
| Windows | `.msi` 或 `.exe` | 安装后启动 `llm-speedway` |
| macOS | `.dmg` | 打开 DMG 后启动应用 |
| Linux | `.AppImage` 或 `.deb` | 直接运行 AppImage，或安装 deb 包 |

如果 Releases 页面暂时没有你需要的平台文件，请使用下面的源码安装方式。

### 源码安装

需要先安装：

- Node.js 20+
- Rust stable
- 当前系统对应的 Tauri 构建依赖

Windows 还需要 Visual Studio Build Tools，并安装 C++ workload。

```bash
git clone https://github.com/YuXiang-ZhuanSun/llm-speedway.git
cd llm-speedway/v2
npm ci
npm run desktop:dev
```

本地构建桌面安装包：

```bash
npm run desktop:build
```

生成的安装包位于 `v2/src-tauri/target/**/release/bundle/`。

## 快速开始

1. 打开 `llm-speedway`。
2. 点击 **Add config**。
3. 填写供应商名称、base URL、模型、API key 和 API 格式。
4. 选择 `OpenAI compatible` 或 `Anthropic compatible`。
5. 点击 **Speedtest**。
6. 对比首 token 延迟、生成速度、多轮速度和成功率。

错误 key、错误模型、假 API、错误 endpoint 都会作为真实失败记录。应用不会伪造测评数字。

## 测什么

| 指标 | 字段 | 含义 |
|---|---|---|
| 首 token 延迟 | `ttft_ms` | 第一段可见 assistant 内容到达所需时间 |
| 生成速度 | `decode_tps` | 首 token 之后估算的 tokens/s |
| 多轮速度 | `multi_turn_decode_tps` | 上下文累积后的生成速度 |

## API 格式

OpenAI-compatible API：

```text
POST /chat/completions
Authorization: Bearer <API_KEY>
```

Anthropic-compatible API：

```text
POST /v1/messages
x-api-key: <API_KEY>
anthropic-version: 2023-06-01
```

## V2 技术架构

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

V2 的技术亮点是：它不是一个浏览器页面加脚本，而是一个真正的本地桌面测评应用。

| 层 | 技术职责 | 为什么重要 |
|---|---|---|
| React + TypeScript | 桌面 UI、供应商表单、结果表格、对比视图 | 让日常测速流程清晰、可扫描、可反复操作 |
| Tauri IPC | 连接前端 UI 和 Rust 原生命令，不需要本地 HTTP 服务 | 避免 CORS 问题，也让应用作为一个桌面产品发布 |
| Rust commands | 暴露供应商管理、测速等 typed app actions | 给前端一个小而稳定的调用边界 |
| Rust services | 处理供应商逻辑、真实 streaming 请求、计时采集、结果归一化 | 测真实 API 行为，不做假数据、不靠估算糊弄 |
| SQLite | 本地保存配置、测评历史和结果 | 方便复测和对比，同时不把数据发到额外服务 |

测速链路是本地原生链路：

```text
用户点击 Speedtest
        |
        v
Tauri command
        |
        v
Rust speedtest service
        |
        v
OpenAI / Anthropic compatible streaming API
        |
        v
Timing metrics -> SQLite -> UI comparison table
```

这套架构要捕捉的是 agent 工作时真正影响体感的细节：第一段可见 token 什么时候到、streaming 后续写得有多快、响应是否真的产生了 assistant 文本、多轮上下文变重后速度是否还稳定。

本地数据存储在：

```text
~/.llm-speedway/llm-speedway.db
```

项目结构：

```text
v1/        # 原 Python CLI 测评工具
v2/        # Tauri + React + Rust 桌面应用
```

## 开发

```bash
cd v2
npm ci
npm run build
npm run desktop:dev
```

Rust 校验：

```bash
cd v2/src-tauri
cargo check
```

## V1

第一版保留在 [`v1/`](v1/)，仍然是可用的 Python CLI 测评工具，会输出 Markdown、CSV 和 JSONL。

## License

MIT
