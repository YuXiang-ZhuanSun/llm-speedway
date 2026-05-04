<p align="center">
  <img src="v1/assets/logo.svg" alt="llm-speedway logo" width="560">
</p>

# llm-speedway

**一个本地桌面 LLM API 延迟基准测试工具：首 token 延迟、持续生成速度、多轮上下文速度，一次测清楚。**

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

`llm-speedway` 测的是用户真正能感受到的 LLM API 速度：模型多久开始输出、开始之后写得多快、上下文变长之后还能不能保持速度。

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

## 架构

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

本地数据存储在：

```text
~/.llm-speedway/llm-speedway.db
```

项目结构：

```text
v1/        # 原 Python CLI 测评工具
v2/        # Tauri + React + Rust 桌面应用
```

## 发布构建

桌面发布由 `.github/workflows/desktop-release.yml` 负责。

推送 `v*` tag，或手动运行 workflow 并输入 release tag，会构建：

- Windows: MSI 和 NSIS EXE
- macOS: DMG
- Linux: AppImage 和 deb 包

workflow 会检查每个平台是否真的产出了安装包。如果构建结束但没有文件，会直接失败，避免发布空 release。

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
