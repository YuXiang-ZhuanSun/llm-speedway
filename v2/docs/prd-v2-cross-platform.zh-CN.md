# llm-speedway V2 跨平台桌面版 PRD

## 1. 背景

`llm-speedway` 第一版是本地 CLI 工具，已经能够通过配置文件调用 OpenAI-compatible Chat Completions API，测量首 token 延迟、生成速度、多轮速度，并输出 Markdown、CSV、JSONL 报告。

第二版希望把这个能力产品化为跨平台桌面软件，让用户不再手写配置文件，而是在图形界面中持续维护多组 API key、模型、API 地址和测速场景，一键执行测速，并以清晰结果帮助用户选择更适合 Agent 使用的 LLM API。

V2 技术架构参考 `cc-Switch`：前端使用 React + TypeScript，桌面壳和后端能力使用 Tauri + Rust，数据以 SQLite 作为单一事实源，设备级设置使用 JSON 存储。

## 2. 产品目标

1. 提供 Windows、macOS、Linux 可安装的桌面应用。
2. 支持用户在 UI 中新增、编辑、删除、复制、排序多组 API 配置。
3. 支持同一供应商下维护不同模型、不同 API endpoint、不同 key。
4. 支持一键测速，测速期间弹出等待窗口展示进度和当前状态。
5. 测速完成后展示可比较、可排序、可导出的结果。
6. 保留第一版核心测速指标：Start latency、Generation speed、Multi-turn speed。
7. 将配置、测速历史、结果数据本地化存储，默认不上传任何数据。

## 3. 目标用户

- 需要比较不同 LLM API 速度的 Agent 开发者。
- 同时使用多个模型供应商的个人用户或团队成员。
- 需要快速判断某个 API key、模型或 endpoint 是否可用、是否稳定的用户。
- 需要把测速结果留档、复测、导出给团队讨论的用户。

## 4. 使用场景

### 4.1 新增 API 配置

用户打开应用后，点击“添加配置”，填写供应商名称、模型名称、API base URL、API key、endpoint、备注等信息。保存后，该配置出现在主列表中，可继续添加更多配置。

### 4.2 对单个模型测速

用户在配置列表中选择某一行，点击“测速”。系统弹出等待窗口，显示连接检查、短对话、长生成、多轮测试等阶段。完成后展示本次结果。

### 4.3 批量测速并比较

用户勾选多个配置，点击“批量测速”。系统按并发设置执行测速，并在结果页按首 token 延迟、生成速度、多轮速度、成功率等维度排序。

### 4.4 编辑配置后复测

用户修改模型、endpoint 或 key 后，可直接点击复测。系统记录不同时间的测速历史，便于比较同一配置在不同时间的表现。

### 4.5 导出结果

用户可将测速结果导出为 Markdown、CSV、JSONL，兼容第一版产物结构，便于归档或放入仓库。

## 5. 功能范围

### 5.1 配置管理

#### 必须支持

- 新增 API 配置。
- 编辑 API 配置。
- 删除 API 配置，删除前需要确认。
- 复制已有配置，用于快速创建相似模型。
- 配置排序。
- 配置搜索和筛选。
- 启用/禁用配置。
- API key 输入框默认隐藏，支持点击显示。
- 支持 key 可用性快速验证。

#### 配置字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| id | string | 是 | 本地唯一 ID |
| provider_name | string | 是 | 供应商名称，如 DeepSeek、OpenAI、Ark |
| display_name | string | 是 | 用户可读配置名称 |
| base_url | string | 是 | API base URL |
| endpoint | string | 是 | 默认 `/chat/completions` |
| api_key | secret string | 是 | 本地加密或受保护存储 |
| model | string | 是 | 模型名称 |
| enabled | boolean | 是 | 是否参与批量测速 |
| tags | string[] | 否 | 标签 |
| note | string | 否 | 备注 |
| created_at | datetime | 是 | 创建时间 |
| updated_at | datetime | 是 | 更新时间 |

### 5.2 测速

#### 单配置测速

- 从配置列表、配置详情、结果详情均可发起。
- 测速前校验必填字段。
- 测速期间禁止重复点击同一配置测速。
- 支持取消本次测速。
- 失败时显示明确错误原因。

#### 批量测速

- 支持勾选多个配置后批量运行。
- 支持设置最大并发数，默认 2。
- 支持失败继续执行其他配置。
- 支持查看每个配置当前阶段。

#### 测试阶段

1. 连接检查：验证 base URL、endpoint、key、model 是否可调用。
2. 短对话：测量首 token 延迟。
3. 长生成：测量首 token 后的持续生成速度。
4. 多轮对话：测量上下文累积后的速度变化。
5. 汇总：计算指标并写入本地历史。

#### 核心指标

| 指标 | 字段 | 说明 |
|---|---|---|
| Start latency | ttft_ms | 第一段可见 assistant 内容到达时间 |
| Generation speed | decode_tps | 首 token 后的 tokens/s |
| Multi-turn speed | multi_turn_decode_tps | 多轮上下文中的 tokens/s |
| Total latency | total_latency_ms | 请求完整耗时，辅助调试 |
| Success rate | success_rate | 多次运行成功比例 |
| Error summary | error_message | 失败原因摘要 |

### 5.3 等待窗口

用户点击测速后出现模态窗口。

#### 必须展示

- 当前测试对象：供应商、模型、base URL。
- 当前阶段：连接检查、短对话、长生成、多轮、汇总。
- 进度条或步骤状态。
- 已耗时。
- 可取消按钮。
- 简短状态文本。

#### 状态示例

- 正在连接 API
- 正在等待首 token
- 正在计算生成速度
- 正在执行第 2 轮多轮测试
- 正在保存结果
- 测速失败：401 Unauthorized

### 5.4 结果展示

#### 列表视图

主结果页以表格展示最近测速结果。

| 列 | 说明 |
|---|---|
| 配置名称 | display_name |
| 供应商 | provider_name |
| 模型 | model |
| 首 token | ttft_ms |
| 生成速度 | decode_tps |
| 多轮速度 | multi_turn_decode_tps |
| 状态 | success / failed / canceled |
| 测试时间 | created_at |

#### 详情视图

- 展示本次测速的完整阶段结果。
- 展示每个 scenario 的原始指标。
- 展示错误详情。
- 支持复制结果摘要。
- 支持导出 Markdown、CSV、JSONL。

#### 比较视图

- 支持选择多条结果进行对比。
- 支持按任意指标排序。
- 推荐展示“最快首 token”“最快长生成”“多轮最稳定”等轻量结论。

### 5.5 历史记录

- 所有测速任务都写入历史。
- 支持按供应商、模型、标签、日期、状态筛选。
- 支持删除单条历史。
- 支持清空历史，需二次确认。
- 支持结果归档导出。

### 5.6 设置

- 并发数。
- 默认运行次数。
- 请求超时时间。
- 是否启用 warmup。
- 结果保存目录。
- 是否自动检查更新。
- 主题：跟随系统、浅色、深色。
- 代理设置。

## 6. 非功能需求

### 6.1 跨平台

- 支持 Windows 10/11。
- 支持 macOS 13+。
- 支持主流 Linux 桌面发行版。
- 构建产物应包含安装包或可执行文件。

### 6.2 安全

- API key 默认只保存在本机。
- UI 默认隐藏 API key。
- 日志、导出文件、错误信息不得默认泄露完整 API key。
- 可在必要时只展示 key 的前后少量字符，如 `sk-...abcd`。
- 后续可评估使用系统 keychain；MVP 可先使用本地加密或受保护 SQLite 字段。

### 6.3 稳定性

- 测速任务失败不能导致应用崩溃。
- 数据写入必须具备原子性。
- SQLite 访问需要并发保护。
- 应用启动时如果数据库损坏，需要提示用户并尝试备份恢复。

### 6.4 性能

- 1000 条配置和 10000 条历史记录下，主列表操作应保持流畅。
- 批量测速时 UI 不应卡死。
- 大结果导出应在后台执行并显示状态。

### 6.5 隐私

- 除用户配置的 LLM API endpoint 外，应用不向其他服务发送 prompt、key 或结果。
- 如未来加入自动更新或遥测，需要独立开关和明确说明。

## 7. 技术架构

### 7.1 总体架构

```text
┌─────────────────────────────────────────────────────────────┐
│                    前端 (React + TS)                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ Components  │  │    Hooks     │  │  TanStack Query  │    │
│  │   UI 层      │──│  业务逻辑     │──│   缓存/同步       │    │
│  └─────────────┘  └──────────────┘  └──────────────────┘    │
└────────────────────────┬────────────────────────────────────┘
                         │ Tauri IPC
┌────────────────────────▼────────────────────────────────────┐
│                  后端 (Tauri + Rust)                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │  Commands   │  │   Services   │  │  Models/Config   │    │
│  │   API 层     │──│   业务层      │──│    数据层         │    │
│  └─────────────┘  └──────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 核心设计模式

- SSOT：所有可同步业务数据存储在 `~/.llm-speedway/llm-speedway.db`。
- 双层存储：SQLite 存储配置、测速任务、历史结果；JSON 存储设备级设置。
- 原子写入：导出、备份、JSON 设置使用临时文件 + 重命名。
- 并发安全：Rust 后端使用 Mutex 或连接池保护数据库访问。
- 分层架构：Commands -> Services -> DAO -> Database。
- IPC 边界清晰：前端不直接处理文件系统和数据库。

### 7.3 推荐目录结构

```text
src/
  components/
  hooks/
  pages/
  routes/
  services/
  types/
src-tauri/
  src/
    commands/
    services/
    dao/
    models/
    database/
    config/
    speedtest/
```

### 7.4 后端服务

| 服务 | 职责 |
|---|---|
| ProviderService | API 配置增删改查、复制、排序、启用禁用 |
| SpeedtestService | API 端点延迟测量、场景执行、指标汇总 |
| ResultService | 测速结果查询、比较、删除、导出 |
| ConfigService | 应用设置、导入导出、备份轮换 |
| SecretService | API key 存储、脱敏、读取 |
| SessionManager | 运行中测速任务管理、取消、进度事件 |

### 7.5 前端模块

| 模块 | 职责 |
|---|---|
| ProviderList | 配置列表、搜索、筛选、批量选择 |
| ProviderEditor | 新增和编辑配置 |
| SpeedtestDialog | 等待窗口、进度、取消 |
| ResultTable | 结果列表、排序 |
| ResultDetail | 结果详情、错误详情、导出 |
| CompareView | 多结果比较 |
| SettingsPage | 全局设置 |

### 7.6 数据库表草案

#### providers

```sql
CREATE TABLE providers (
  id TEXT PRIMARY KEY,
  provider_name TEXT NOT NULL,
  display_name TEXT NOT NULL,
  base_url TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  api_key_cipher TEXT NOT NULL,
  model TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1,
  sort_order INTEGER NOT NULL DEFAULT 0,
  tags_json TEXT NOT NULL DEFAULT '[]',
  note TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

#### speedtest_runs

```sql
CREATE TABLE speedtest_runs (
  id TEXT PRIMARY KEY,
  provider_id TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  ttft_ms REAL,
  decode_tps REAL,
  multi_turn_decode_tps REAL,
  total_latency_ms REAL,
  success_rate REAL,
  error_message TEXT,
  summary_json TEXT NOT NULL DEFAULT '{}',
  raw_result_path TEXT,
  FOREIGN KEY(provider_id) REFERENCES providers(id)
);
```

#### speedtest_samples

```sql
CREATE TABLE speedtest_samples (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  scenario TEXT NOT NULL,
  attempt_index INTEGER NOT NULL,
  success INTEGER NOT NULL,
  ttft_ms REAL,
  decode_tps REAL,
  total_latency_ms REAL,
  error_message TEXT,
  raw_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES speedtest_runs(id)
);
```

## 8. 交互流程

### 8.1 新增配置流程

```text
点击添加配置
  -> 打开编辑表单
  -> 填写 provider、base_url、api_key、model
  -> 可选点击验证
  -> 保存
  -> 返回配置列表
```

### 8.2 单个测速流程

```text
点击测速
  -> 前端调用 create_speedtest_run
  -> 后端创建任务并返回 run_id
  -> 前端打开 SpeedtestDialog
  -> 后端通过事件推送进度
  -> 完成后写入数据库
  -> 前端刷新结果并展示详情
```

### 8.3 取消测速流程

```text
点击取消
  -> 前端调用 cancel_speedtest_run(run_id)
  -> 后端标记取消并中断后续请求
  -> 当前请求如无法立即中断，等待超时或响应结束
  -> 状态写入 canceled
```

## 9. MVP 范围

### 必须交付

- Tauri + React + TypeScript 项目骨架。
- SQLite 数据库初始化和迁移。
- API 配置 CRUD。
- 单个配置测速。
- 等待弹窗和取消按钮。
- 结果表格和结果详情。
- Markdown、CSV 导出。
- Windows/macOS/Linux 构建配置。

### 暂不纳入 MVP

- 云同步。
- 团队协作。
- 自动化定时测速。
- 完整系统 keychain 适配。
- 插件市场。
- 非 OpenAI-compatible 协议的深度适配。

## 10. 验收标准

1. 用户可以在 UI 中添加至少 10 个不同 API 配置。
2. 用户可以对任意单个配置发起测速，并看到等待窗口。
3. 测速完成后，结果中包含首 token 延迟、生成速度、多轮速度。
4. API key 不会在列表、日志、导出摘要中明文展示。
5. 应用重启后，配置和历史结果仍然存在。
6. 网络错误、401、404、模型不存在、超时等错误均能被展示为可理解信息。
7. 批量测速失败一个配置时，不影响其他配置继续执行。
8. Windows、macOS、Linux 至少各能生成一个可运行构建产物。

## 11. 版本规划

### V2.0 MVP

- 桌面端基础可用。
- 配置管理。
- 单个测速。
- 结果查看和导出。

### V2.1

- 批量测速。
- 多结果比较。
- 高级筛选。
- 结果趋势图。

### V2.2

- 更完善的密钥存储。
- 配置导入导出。
- 备份轮换。
- 更多 provider adapter。

### V2.3

- 定时测速。
- 结果基线对比。
- 异常波动提醒。

## 12. 风险与待确认

| 风险 | 影响 | 建议 |
|---|---|---|
| API key 本地安全策略不明确 | 影响用户信任 | MVP 先脱敏和本地保护，后续接入系统 keychain |
| 不同供应商 streaming 格式有差异 | 影响指标准确性 | 先限定 OpenAI-compatible，并建立 adapter 测试集 |
| Tauri 跨平台构建复杂 | 影响交付节奏 | 先以 Windows 为主开发，再补 macOS/Linux CI |
| 大批量测速可能触发限流 | 影响结果稳定 | 提供并发数、重试、超时设置 |
| token 计数可能与供应商计费不同 | 影响精确性 | 明确指标用于速度比较，不作为计费依据 |

## 13. 开放问题

1. V2 是否继续沿用 `llm-speedway` 名称，还是需要一个面向桌面端的新产品名？
2. API key MVP 阶段是否接受 SQLite 加密字段，还是第一版桌面端就必须接入系统 keychain？
3. 是否需要兼容第一版 `configs/*.json` 的一键导入？
4. 是否需要保留 CLI，让桌面端调用同一测速内核，还是直接在 Rust 中重写测速逻辑？
5. 默认测速 prompt 是否沿用第一版 `scenarios/`，还是需要为桌面用户新增更短、更省成本的默认场景？
