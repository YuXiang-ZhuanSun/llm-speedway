# V2 发布型桌面应用架构

V2 的最终形态是一个可安装、可发布的 Tauri 桌面应用，而不是“本地前端 + 本地后端服务”。

## 运行模型

```text
用户启动安装后的 llm-speedway
        |
        v
Tauri 桌面进程
        |
        +-- WebView: React + TypeScript UI
        |
        +-- Rust Core: commands / services / database / speedtest
        |
        +-- 本地数据: ~/.llm-speedway/llm-speedway.db
```

前端不访问 `localhost:1421` 之类的本地 HTTP 服务。所有业务调用通过 Tauri IPC：

```ts
invoke("list_providers")
invoke("create_provider", { input })
invoke("run_speedtest", { providerId })
```

## 分层

```text
src/
  components/              # UI
  hooks/                   # 业务 hooks
  lib/api/                 # Tauri invoke 封装
  types.ts                 # 前端类型

src-tauri/src/
  commands/                # Tauri command API
  services/                # 业务逻辑
  database/                # SQLite 初始化与连接管理
  models/                  # Rust 数据模型
  state.rs                 # 应用级状态注入
```

## 数据

- SQLite: `~/.llm-speedway/llm-speedway.db`
- 设备级设置: 后续放入 `~/.llm-speedway/settings.json`
- 备份: 后续放入 `~/.llm-speedway/backups/`

## 发布

仓库已准备 GitHub Actions 工作流：

```text
.github/workflows/desktop-release.yml
```

推送 `v*` tag 或手动触发 workflow 后，会在 Windows、macOS、Linux 上构建 Tauri 安装包，并创建 draft release。

## 当前状态

已完成：

- V1 移入 `v1/`
- V2 Tauri 项目骨架
- React UI 壳
- Tauri IPC API 封装
- Rust commands / services / database / models 分层
- SQLite 初始化
- GitHub Actions 桌面端 release 工作流

待完成：

- 真实 OpenAI-compatible streaming 测速
- API key 加密或系统 keychain
- 设置 JSON 原子写入
- 导入 V1 configs
- 结果导出 Markdown / CSV / JSONL
- macOS 签名与公证
- Windows 签名
