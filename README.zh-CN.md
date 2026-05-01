<p align="center">
  <img src="assets/logo.svg" alt="llm-speedway logo" width="560">
</p>

# llm-speedway

**找到真正让 Agent 变快的 LLM API：启动延迟、生成速度、多轮速度，一份报告讲清楚。**

<p>
  <a href="README.md">English</a>
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

Agent 的慢，往往不是抽象的慢，而是让用户长时间盯着空白界面。

`llm-speedway` benchmark 的正是这部分体验：模型多久开始输出、开始输出后写得多快、当对话上下文累积后还能不能保持速度。它不是把一堆指标倒进表格，而是生成一份能直接帮助你选模型的报告。

## 它是什么

`llm-speedway` 是一个本地运行的 OpenAI-compatible Chat Completions API 测速工具。

它会发送受控 prompt，监听 streaming 响应，记录首 token 时间，确认接口确实返回了可见 assistant 文本，然后写出：

```text
results/<model>/
  report.md          # 给人看的报告
  summary.csv        # 三个核心指标
  raw_results.jsonl  # 完整请求级数据
```

除了你配置的 API endpoint，数据不会发往其他地方。

## 评价模型

`llm-speedway` 把**原始字段**和**核心指标**分开。原始记录保留调试需要的时间细节，但 benchmark 对外只提升三个速度信号。

| 指标 | 来源 | 含义 | 用来看什么 |
|---|---|---|---|
| **Start latency** | `ttft_ms` | 第一个可见 assistant token 到达的时间 | Agent 开始说话快不快 |
| **Generation speed** | `long_generation.decode_tps` | 长回答场景下，首 token 之后的 tokens/s | 模型持续写得快不快 |
| **Multi-turn speed** | `multi_turn.decode_tps` 按轮次观察 | 上下文累积时的生成速度 | 对话变重后还能不能保持速度 |

### 关于 Completion time

`total_latency_ms` 仍然会记录在每次请求里，但它不是对外主打的 benchmark 指标。

Completion time 会受到回复长度、停止行为、provider 截断策略影响。它适合排查某一次运行，不适合作为跨模型 headline speed signal。想看持续输出，看 **Generation speed**。想看上下文变重后的 Agent 体验，看 **Multi-turn speed**。

这就是项目要讲清楚的事：Agent UX 不是一个数字。

## 测试场景

内置场景很少，因为每一个都对应一个真实 Agent 痛点。

| 场景 | 测什么 | 怎么读 |
|---|---|---|
| `short_chat` | 轻量问答的响应感 | 主要看 Start latency |
| `long_generation` | 长输出的持续生成 | 主要看 Generation speed |
| `multi_turn` | 上下文累积后的退化 | 逐轮比较上下文变重后的指标变化 |

这三类覆盖了 Agent 常见的速度问题：开头慢、写得慢、多轮后速度变慢。

`multi_turn` 不是“一个多轮回答”。它是一组连续请求：第 2 轮携带第 1 轮 assistant 回复，第 3 轮携带前两轮上下文，以此类推。它要看的是同一个模型在对话越来越重之后，是否开始变慢。

## 安装

本地安装：

```powershell
pip install -e .
```

也可以直接运行测试：

```powershell
python -m unittest discover -s tests
```

不依赖 OpenAI SDK。OpenAI-compatible adapter 使用 Python 标准库实现。

## 快速开始

复制配置：

```powershell
Copy-Item configs/config.example.json config.json
```

推荐用环境变量放 API key：

```json
{
  "api": {
    "base_url": "https://api.example.com/v1",
    "api_key_env": "LLM_API_KEY",
    "model": "model-name"
  }
}
```

运行：

```powershell
llm-speedway run --config config.json
```

只跑一个场景：

```powershell
llm-speedway run --config config.json --scenario short_chat --runs 3
```

## Benchmark

已提交的小样本报告在 [results](results/README.md)。

| 模型 | 短对话首 token | 长输出生成速度 | 多轮 |
|---|---:|---:|---|
| `deepseek-v4-flash` | 6.33s | 97.6 tok/s | 成功 |
| `doubao-seed-2.0-code` | 15.31s | 105.1 tok/s | 成功 |
| `glm-5.1` | 24.56s | 76.5 tok/s | 第 1 轮失败 |
| `kimi-k2.6` | 11.88s | 68.3 tok/s | 第 1 轮无可见输出 |

这些是第一轮筛选报告，不是严格统计结论。如果需要更稳的数字，提高 `runs_per_scenario`。

## 技术架构

`llm-speedway` 只有一条主链路：**定义测试，调用模型，测量流式响应，写出报告。**

| 阶段 | 模块 | 职责 |
|---|---|---|
| 1. Define | `configs/` + 根目录 `scenarios/` | 选择模型、接口、运行次数和 prompt 形态 |
| 2. Run | `runner.py` | 执行每个场景，保留请求级记录 |
| 3. Call | `providers/` | 调用 OpenAI-compatible streaming API |
| 4. Measure | `core/metrics.py` | 把流式事件转成启动延迟和生成速度 |
| 5. Report | `reports/` + `results/` | 输出 Markdown、CSV、JSONL |

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

代码目录也按同样的边界组织：

```text
llm_speedway/
  cli.py                  # 命令入口
  runner.py               # benchmark 编排
  core/                   # 配置、指标、token 估算
  providers/              # API 协议适配
  scenarios/              # 场景 JSON 加载器
  reports/                # Markdown / CSV / JSONL 输出
configs/                  # 可复用 provider 配置
scenarios/                # 可扩展 benchmark 用例
tests/                    # 指标与汇总测试
results/                  # 已提交的 benchmark 报告
assets/                   # logo 与 README 素材
```

为什么这样拆：

| 层 | 职责 |
|---|---|
| `core/` | 配置解析、指标计算、token 估算 |
| `providers/` | API 协议适配；当前支持 OpenAI-compatible Chat API |
| `llm_speedway/scenarios/` | 场景 JSON 加载与校验 |
| `reports/` | Markdown 和 CSV 输出 |
| `runner.py` | 串联 provider、scenario、metrics、report |

新增 provider 不应该动指标。新增场景不应该动 HTTP。改报告不应该重写原始数据。

## 扩展用例

Benchmark 用例放在 Python 包外：

```text
scenarios/
  short_chat.json
  long_generation.json
  multi_turn.json
```

新增一个 JSON 文件：

```json
{
  "name": "agent_tool_call",
  "description": "工具调用密集型 Agent 任务。",
  "kind": "single_turn",
  "max_tokens": 512,
  "prompts": [
    "为一个 Python CLI 项目规划三步重构方案。"
  ]
}
```

然后在配置中引用：

```json
{
  "benchmark": {
    "scenarios_dir": "scenarios"
  },
  "scenarios": ["agent_tool_call"]
}
```

## 数据模型

每次请求都会生成一条原始记录：

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

报告只提升三个核心指标：

- `ttft_ms` -> Start latency
- `long_generation.decode_tps` -> Generation speed
- `multi_turn.decode_tps` -> Multi-turn speed

`total_latency_ms` 仍然保留在原始记录里，用于调试和复现，但它不是 headline benchmark 指标。

如果 streaming 响应没有任何可见 assistant 内容，这个样本会失败。空回答不应该拥有漂亮数字。

## Roadmap

- Anthropic-compatible provider adapter
- 并发 Agent load 模式
- provider-specific streaming normalization
- 外部 scenario 文件
- HTML 报告导出

## 原则

Fast token matters.

如果 Agent 注定需要时间，它至少应该先开始说话。
