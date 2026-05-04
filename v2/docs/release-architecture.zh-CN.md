# V2 发布说明

V2 的发布形态是可安装的 Tauri 桌面应用，不是“本地前端 + 本地 HTTP 后端”的开发组合。

## 运行模型

```text
用户启动 llm-speedway
        |
        v
Tauri 桌面进程
        |
        +-- WebView: React + TypeScript UI
        |
        +-- Rust Core: commands / services / database / speedtest
        |
        +-- Local data: ~/.llm-speedway/llm-speedway.db
```

前端通过 Tauri IPC 调用 Rust 后端：

```ts
invoke("list_providers")
invoke("create_provider", { input })
invoke("run_speedtest", { providerId })
```

## 发布方式

发布 workflow 位于：

```text
.github/workflows/desktop-release.yml
```

触发方式：

- 推送 `v*` tag，例如 `v0.2.0`
- 在 GitHub Actions 页面手动运行 workflow，并输入 release tag

三平台构建目标：

| 平台 | 构建环境 | 发布文件 |
|---|---|---|
| Windows | `windows-latest` | `.msi`, `.exe` |
| macOS | `macos-latest` | `.dmg` |
| Linux | `ubuntu-22.04` | `.AppImage`, `.deb` |

每个平台构建后都会检查 `v2/src-tauri/target` 下是否真的存在安装包。如果没有文件，workflow 会失败，避免 GitHub Release 为空。

## 正式发版步骤

```bash
git tag v0.2.0
git push origin v0.2.0
```

然后到 GitHub Releases 页面确认：

- Windows 有 `.msi` 或 `.exe`
- macOS 有 `.dmg`
- Linux 有 `.AppImage` 或 `.deb`
- release 说明包含源码安装兜底方式

如果需要手动补发同一个 tag，可以在 GitHub Actions 里运行 `Desktop Release`，输入相同的 release tag。

## 没有 release 文件时

不要让用户猜。README 必须提供源码安装方式：

```bash
git clone https://github.com/YuXiang-ZhuanSun/llm-speedway.git
cd llm-speedway/v2
npm ci
npm run desktop:dev
```

本地构建安装包：

```bash
npm run desktop:build
```

本地构建需要 Node.js 20+、Rust stable 和对应系统的 Tauri 构建依赖。
