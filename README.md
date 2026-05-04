<p align="center">
  <img src="v1/assets/logo.svg" alt="llm-speedway logo" width="560">
</p>

# llm-speedway

**找到真正让 Agent 变快的 LLM API：首 token 延迟、持续生成速度、多轮速度，一次测速看清楚。**

`llm-speedway` 是一个跨平台桌面应用，用来管理多个 LLM API 配置并进行真实测速。你可以添加不同供应商、不同模型、不同 API key 和不同 API 地址，点击测速后直接看到可比较的速度结果。

![llm-speedway desktop screenshot](v2/assets/screenshot.png)

## 功能

- 跨平台桌面应用：Windows、macOS、Linux。
- 多 API 配置管理：供应商、Base URL、模型名、API key、API 格式。
- 同时支持 OpenAI-compatible 与 Anthropic-compatible API。
- 真实 streaming 测速，不伪造结果。
- 每次点击测速都会发起新的真实请求。
- 多个配置的测速结果可同时展开显示。
- 本地 SQLite 保存配置与测速历史。
- 默认不上传数据；除你配置的 API endpoint 外，不向其他服务发送 prompt、key 或结果。

## 测速指标

| 指标 | 含义 | 用来看什么 |
|---|---|---|
| **首 token** | 第一段可见 assistant 内容到达时间 | Agent 是否很快开始响应 |
| **生成速度** | 首 token 之后的估算 tokens/s | 模型持续输出是否足够快 |
| **多轮速度** | 带上下文历史后的估算 tokens/s | 对话变重后是否仍然稳定 |
| **成功率** | 本次测速是否成功 | API key、模型、endpoint 是否可用 |

## 下载安装

前往 GitHub Releases 下载对应系统的安装包：

[下载 llm-speedway Releases](https://github.com/YuXiang-ZhuanSun/llm-speedway/releases)

### Windows

下载 `.msi` 安装包并双击安装。

也可以下载 portable 版本，解压后直接运行 `llm-speedway.exe`。

### macOS

下载 `.dmg`，拖入 Applications 后启动。

如果 macOS 提示应用来自未知开发者，可在“系统设置 -> 隐私与安全性”中允许打开。正式发布签名后会减少这个提示。

### Linux

根据发行版选择：

- Debian / Ubuntu：下载 `.deb`
- Fedora / RHEL：下载 `.rpm`
- 通用桌面发行版：下载 `.AppImage`

AppImage 需要赋予执行权限：

```bash
chmod +x llm-speedway*.AppImage
./llm-speedway*.AppImage
```

## 使用方法

1. 打开 `llm-speedway`。
2. 点击“添加配置”。
3. 填写供应商、Base URL、模型名、API key。
4. 选择 API 格式：
   - `OpenAI compatible`
   - `Anthropic compatible`
5. 点击“测速”。
6. 等待测速完成，查看首 token、生成速度、多轮速度和成功率。

如果填写了假的 API、错误 key、错误模型名或错误 endpoint，测速会失败并显示真实错误信息。

## API 格式

### OpenAI-compatible

默认 endpoint：

```text
/chat/completions
```

请求使用：

```text
Authorization: Bearer <API_KEY>
```

### Anthropic-compatible

默认 endpoint：

```text
/v1/messages
```

请求使用：

```text
x-api-key: <API_KEY>
anthropic-version: 2023-06-01
```

## 本地数据

V2 使用 Tauri + Rust 后端，配置和测速历史保存在本机 SQLite 数据库中。

```text
~/.llm-speedway/llm-speedway.db
```

不会单独启动本地 HTTP 后端服务。桌面 UI 通过 Tauri IPC 调用 Rust 后端。

## 开发

V2 源码位于 [`v2/`](v2/)。

安装依赖：

```powershell
cd v2
npm install
```

运行桌面开发版：

```powershell
npm run desktop:dev
```

构建桌面安装包：

```powershell
npm run desktop:build
```

仅预览前端：

```powershell
npm run dev
```

浏览器预览模式也会尝试真实测速，但会受到 API 服务 CORS 限制。桌面版不受 CORS 限制。

## 项目结构

```text
v1/        # 第一版 Python CLI，保留历史实现
v2/        # 第二版 Tauri 桌面应用
```

V1 是本地 CLI benchmark runner，已移动到 [`v1/`](v1/)。

V2 是当前主线，技术栈：

- React + TypeScript
- Tauri + Rust
- SQLite
- TanStack Query

## 发布

仓库包含 GitHub Actions 桌面端发布工作流：

```text
.github/workflows/desktop-release.yml
```

推送 `v*` tag 后会构建 Windows、macOS、Linux 安装包，并创建 GitHub draft release。

## License

MIT
