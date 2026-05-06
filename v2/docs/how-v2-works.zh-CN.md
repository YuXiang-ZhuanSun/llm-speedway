# llm-speedway V2 实现导读

这份文档不是 API 手册，而是一条读代码路线。目标很简单：你不需要先懂 Tauri、Rust 或 React 的全部细节，也能顺着一次真实的测速流程，看懂 V2 程序是怎么跑起来的。

建议先记住一句话：

```text
React 负责展示和交互，Tauri IPC 负责把前端请求送到 Rust，Rust 负责真实测速和本地存储。
```

## 先补基础概念

如果你是 0 基础，可以先把 V2 想象成一家小餐厅：

```text
用户                 点菜的人
React UI             前台菜单和收银台
Tauri IPC            前台递给后厨的小票通道
Rust command         后厨接小票的窗口
Rust service         真正做菜的人
SQLite               店里的账本和库存本
外部 LLM API          供应商
测速结果              最后端上来的菜和账单
```

下面这些词后面会反复出现。先不用背，读到代码时回来对照就行。

| 概念 | 它的功能 | 抽象模型 |
|---|---|---|
| 桌面应用 | 安装在电脑上的程序，有自己的窗口、菜单、文件和本地数据 | 一间开在你电脑里的小店 |
| Tauri | 把 Web 前端和 Rust 本地能力打包成桌面应用的框架 | 店面装修 + 前台和后厨之间的内部通道 |
| WebView | 桌面窗口里用来显示网页 UI 的容器 | 桌面应用里的“小浏览器屏幕” |
| React | 用组件拼 UI 的前端库 | 用积木搭界面 |
| Component | React 里的 UI 小模块，比如按钮、表单、结果卡片 | 一块可复用的积木 |
| State | 前端记住的当前状态，比如搜索词、弹窗是否打开、哪个 provider 正在测速 | 前台桌面上的临时便签 |
| TypeScript | 给 JavaScript 加类型，提前告诉代码“这个值应该长什么样” | 表格里的字段说明 |
| TanStack Query | 管理远程/异步数据读取、缓存和刷新 | 前台的资料夹，知道哪些数据要重新拿 |
| API adapter | 前端调用后端前的一层包装 | 前台统一把需求写成标准小票 |
| IPC | Inter-Process Communication，进程间通信 | 前台和后厨之间传小票 |
| `invoke` | Tauri 前端调用 Rust command 的函数 | 把小票递进后厨窗口 |
| Rust command | 暴露给前端调用的 Rust 函数 | 后厨接单窗口 |
| Service | 放真正业务逻辑的 Rust 模块 | 后厨里真正干活的人 |
| Model | 描述数据长什么样的结构 | 一张固定格式的表单 |
| SQLite | 一个轻量本地数据库，数据存在本机文件里 | 店里的账本 |
| Provider | 一个 LLM API 配置，比如供应商、base URL、model、API key | 一家可调用的模型供应商档案 |
| Benchmark | 用固定方法测性能 | 用同一套尺子量不同供应商 |
| Streaming | API 不等全文生成完，而是一段一段吐回来 | 水龙头慢慢出水，而不是等满一桶再给你 |
| TTFT | Time To First Token，第一个可见 token 出现前等了多久 | 打开水龙头后第一滴水出来前等多久 |
| TPS | Tokens Per Second，每秒生成多少 token | 水流速度 |
| Error handling | 失败时不假装成功，而是记录错误 | 小票失败也要记账，方便复盘 |

再用一句更工程化的话总结：

```text
前端负责“用户想做什么”，后端负责“这件事怎么真实发生”，数据库负责“发生过什么要留下来”。
```

## 先看大地图

V2 是一个桌面应用，但它不是“前端页面 + 本地 HTTP 后端”。它是 Tauri 应用：

```text
用户看到的桌面窗口
        |
        v
WebView 里的 React UI
        |
        | invoke("run_speedtest", { providerId })
        v
Tauri IPC
        |
        v
Rust command
        |
        v
Rust service
        |
        +--> SQLite 本地数据库
        |
        +--> OpenAI / Anthropic compatible streaming API
```

对应到代码目录：

```text
v2/src/                         # React + TypeScript 前端
v2/src/lib/api/desktop.ts        # 前端和 Tauri/Rust 的连接层
v2/src-tauri/src/lib.rs          # Tauri 启动、注册 commands、初始化状态
v2/src-tauri/src/commands/       # 暴露给前端调用的 Tauri commands
v2/src-tauri/src/services/       # 真正的业务逻辑：provider 管理、测速
v2/src-tauri/src/database/       # SQLite 初始化和连接管理
v2/src-tauri/src/models/         # Rust 和前端共享语义的数据结构
```

如果你只想最快看懂主流程，按这个顺序读：

1. `v2/src/App.tsx`
2. `v2/src/lib/api/desktop.ts`
3. `v2/src-tauri/src/lib.rs`
4. `v2/src-tauri/src/commands/speedtests.rs`
5. `v2/src-tauri/src/services/speedtest_service.rs`
6. `v2/src-tauri/src/database/mod.rs`

## 程序怎么启动

“启动程序”本质上是把两套东西一起跑起来：

```text
一套是用户能看到、能点击的界面。
一套是用户看不见、但负责读写数据库和请求 API 的本地能力。
```

桌面开发时，我们运行：

```bash
cd v2
npm run desktop:dev
```

这个命令来自 `v2/package.json`，实际执行的是：

```bash
tauri dev
```

Tauri 会同时做两件事：

1. 启动 React/Vite 前端，让 UI 跑在 WebView 里。
2. 编译并启动 Rust 进程，让本地能力、数据库和 HTTP 测速服务可用。

这里的 Vite 可以理解成“前端开发服务器”。开发时它负责把 `App.tsx`、CSS、图片等资源快速打包并送进 WebView。Rust 进程则像应用的本地引擎，负责那些浏览器页面不擅长或不应该直接做的事，比如稳定地发 HTTP streaming 请求、写 SQLite 数据库。

Rust 的入口在 `v2/src-tauri/src/main.rs`，它只做一件事：调用 `llm_speedway_v2_lib::run()`。真正的应用装配在 `v2/src-tauri/src/lib.rs`。

`lib.rs` 里最重要的是两段：

```rust
let database = Database::open(app.handle())?;
app.manage(AppState {
    provider_service: ProviderService::new(database.clone()),
    speedtest_service: SpeedtestService::new(database),
});
```

这表示应用启动时会打开 SQLite，并把两个 service 放进全局 `AppState`：

- `ProviderService`：负责 provider 配置的增删查。
- `SpeedtestService`：负责真实测速和保存结果。

`AppState` 可以理解成“后厨的公共工具箱”。每个 command 被调用时，都可以从这个工具箱里拿到已经准备好的 service，而不是每次重新创建数据库连接和 HTTP client。

接着 `invoke_handler` 注册前端可以调用的命令：

```rust
commands::providers::list_providers
commands::providers::create_provider
commands::providers::duplicate_provider
commands::providers::delete_provider
commands::speedtests::list_speedtest_results
commands::speedtests::run_speedtest
```

所以前端不是随便调用 Rust 函数，只能调用这里注册过的 command。

这个限制反而是好事。它让前端和后端之间有一条清楚的边界：前端只能发出这些明确动作，Rust 只需要维护这些动作的行为。

## 前端在做什么

前端的核心任务不是“算测速结果”，而是“让用户能操作测速流程”。它关心的是页面上现在应该显示什么，以及用户点了按钮后下一步该触发什么。

前端主文件是 `v2/src/App.tsx`。它承担三件事：

1. 读取 provider 列表。
2. 读取测速结果列表。
3. 响应用户操作，比如新增配置、删除配置、点击测速。

如果你打开 `App.tsx` 时看到部分中文 UI 文案是乱码，先不用被它带偏。那是文案编码/显示层面的问题，不影响我们理解程序结构。读主链路时，重点看函数、状态、调用关系和数据流。

这里用了 TanStack Query，所以你会看到：

```ts
const providersQuery = useQuery({ queryKey: ["providers"], queryFn: listProviders });
const resultsQuery = useQuery({ queryKey: ["speedtest-results"], queryFn: listResults });
```

这两行的意思是：

- `providers` 这份数据由 `listProviders()` 提供。
- `speedtest-results` 这份数据由 `listResults()` 提供。
- 后续新增、删除、测速成功后，可以通过 `invalidateQueries` 或 `setQueryData` 刷新 UI。

把 TanStack Query 想成一个数据管家：它知道 provider 列表从哪里来，也知道测速结果从哪里来。组件不需要自己到处维护“数据是不是过期了”，只要告诉管家“这份数据该刷新了”。

`useState` 则是 React 自己的便签纸。比如：

```ts
const [query, setQuery] = useState("");
const [isEditorOpen, setIsEditorOpen] = useState(false);
```

这表示：

- `query` 记录搜索框当前输入了什么。
- `isEditorOpen` 记录新增配置弹窗是否打开。
- 调用 `setQuery()` 或 `setIsEditorOpen()` 后，React 会重新计算页面该怎么显示。

点击测速时，代码会进入 `handleRunSpeedtest(provider)`：

```ts
function handleRunSpeedtest(provider: ProviderConfig) {
  setExpandedProviderIds((current) => new Set(current).add(provider.id));
  setActiveRuns((current) => ({
    ...current,
    [provider.id]: { provider, stage: "connection", startedAt: Date.now() },
  }));
  runSpeedtestMutation.reset();
  runSpeedtestMutation.mutate(provider.id);
}
```

这段代码先更新 UI 状态，让这一行展开并显示“正在测速”；然后调用 `runSpeedtestMutation.mutate(provider.id)`，真正开始测速。

这里的 `mutation` 可以理解成“会改变世界的动作”。读取列表是 query，新增 provider、删除 provider、运行测速都是 mutation，因为它们会改变数据库或结果列表。

注意一个小细节：前端的进度条不来自 Rust 实时事件。`activeRuns` 只是前端本地状态，配合一个定时器在 `connection -> short_chat -> long_generation -> multi_turn -> summary` 之间推进。它给用户一个正在运行的反馈，但真实结果要等 Rust command 返回。

测速成功后，`runSpeedtestMutation` 的 `onSuccess` 会做三件事：

1. 展开当前 provider 的结果区。
2. 从 `activeRuns` 里移除这个运行中的任务。
3. 把返回的 `SpeedtestResult` 放进 `speedtest-results` 缓存，并重新拉取结果列表。

## 前端怎么调用 Rust

前端不会在 `App.tsx` 里直接写 `invoke`。中间有一层适配器：`v2/src/lib/api/desktop.ts`。

这层很重要，因为它把“前端想做什么”和“运行环境怎么做”分开了。

所谓“适配器”，就是把复杂差异藏起来，给外面一个稳定按钮。`App.tsx` 只需要调用 `runSpeedtest(providerId)`，不用关心现在是在 Tauri 桌面里，还是在普通浏览器预览里。

```ts
const isTauriRuntime = "__TAURI_INTERNALS__" in window;
```

如果当前在 Tauri 桌面环境里，就调用 Rust：

```ts
export async function runSpeedtest(providerId: string): Promise<SpeedtestResult> {
  if (isTauriRuntime) {
    return invoke("run_speedtest", { providerId });
  }

  const provider = browserProviders.find((item) => item.id === providerId);
  if (!provider) throw new Error("Provider not found");

  const result = await runBrowserSpeedtest(provider);
  browserResults = [result, ...browserResults];
  return result;
}
```

如果只是在浏览器里预览，就走 mock 数据和浏览器 `fetch`。这就是为什么 V2 既能作为桌面应用跑，也能在浏览器里做开发预览。

mock 数据就是“假数据样板”。它的价值是：即使你没有真实 API key，也能先把界面、按钮、列表、结果卡片调通。

真正发布出去的桌面版本，核心路径是：

```text
App.tsx
  -> runSpeedtestMutation
  -> runSpeedtest(provider.id)
  -> invoke("run_speedtest", { providerId })
  -> Rust command
```

## Rust command 是什么

Tauri command 是前端和 Rust 的边界。它的特点是：函数加上 `#[tauri::command]`，然后在 `lib.rs` 里注册，前端就能通过 `invoke("command_name")` 调用。

从抽象上看，command 像一个很薄的服务窗口。它不应该塞太多业务逻辑，只负责三件事：

```text
接前端参数
拿到 AppState 里的 service
把 service 的结果返回给前端
```

测速 command 在 `v2/src-tauri/src/commands/speedtests.rs`：

```rust
#[tauri::command]
pub async fn run_speedtest(
    provider_id: String,
    state: State<'_, AppState>,
) -> Result<SpeedtestResult, String> {
    state
        .speedtest_service
        .run(&provider_id)
        .await
        .map_err(|error| error.to_string())
}
```

这段非常薄。它不做测速，只做转发：

```text
前端传 providerId
        |
        v
run_speedtest command
        |
        v
state.speedtest_service.run(providerId)
```

这种写法是刻意的：command 层只负责“接请求、拿 state、返回结果”。业务逻辑放在 service 层。

这样做的好处是，未来如果我们要给测速加队列、加日志、加更复杂的错误处理，主要改 `SpeedtestService`，不需要把 Tauri command 写成一大坨。

## SpeedtestService 怎么测速

核心文件是 `v2/src-tauri/src/services/speedtest_service.rs`。

Service 是业务逻辑的家。你可以把它理解成“这个功能真正发生的地方”。前端说“我要测速”，command 接到小票，最后真正决定怎么测、测几次、怎么解析、怎么保存的，就是 `SpeedtestService`。

入口是：

```rust
pub async fn run(&self, provider_id: &str) -> rusqlite::Result<SpeedtestResult>
```

它做五步：

```text
1. load_provider(provider_id)
2. 生成 run_id 和 started_at
3. measure_provider(provider)
4. 把成功或失败包装成 SpeedtestResult
5. save_result(result)
```

代码结构大概是：

```rust
let provider = self.load_provider(provider_id)?;
let run_id = Uuid::new_v4().to_string();
let started_at = now_string();

let measured = self.measure_provider(&provider).await;
let finished_at = now_string();

let result = match measured {
    Ok(metrics) => SpeedtestResult { status: "success".to_string(), ... },
    Err(error) => SpeedtestResult { status: "failed".to_string(), ... },
};

self.save_result(&result, &started_at, &finished_at)?;
Ok(result)
```

这里有个关键设计：即使测速失败，也会生成一条 `SpeedtestResult` 并保存到数据库。错误 key、错误模型、错误 endpoint 都不会被偷偷吞掉，而是作为真实失败记录下来。

这对 benchmark 很重要。一个供应商如果经常失败，它的失败本身就是性能数据的一部分。只展示成功结果，会让工具变得不可信。

## 三次请求测三个信号

`measure_provider()` 会连续跑三次请求：

```rust
let short = self.measure_request(...).await?;
let long = self.measure_request(...).await?;
let multi = self.measure_request(...).await?;
```

它们分别对应：

| 请求 | 目的 | 最后使用的指标 |
|---|---|---|
| short chat | 测首 token 什么时候出现 | `ttft_ms` |
| long generation | 测长一点的持续生成速度 | `decode_tps` |
| multi-turn | 测带历史上下文后的生成速度 | `multi_turn_decode_tps` |

所以 V2 不是只测一次请求然后给一个“总耗时”。它关心的是 agent 体验里更关键的三件事：

- 第一个可见 token 来得快不快。
- 后面持续生成快不快。
- 上下文变长以后还稳不稳。

为什么要分三次？因为“慢”不是一种慢。

```text
首 token 慢：用户盯着空白区域等，最难受。
持续生成慢：已经开始说了，但一句话吐很久。
多轮变慢：刚开始还行，一旦上下文多了就拖垮。
```

Agent 产品里这三种慢都会出现，所以 V2 把它们分开测。

## measure_request 的真实工作

`measure_request()` 是测速最核心的函数。它先根据 provider 配置拼 URL：

```rust
let url = join_url(&provider.base_url, &provider.endpoint);
```

然后根据 `api_format` 组装请求体：

- OpenAI compatible：`POST /chat/completions`
- Anthropic compatible：`POST /v1/messages`

HTTP 可以理解成“客户端向服务器发请求的格式”。我们的应用是客户端，LLM API 是服务器。`POST` 表示“我要提交一份数据给你处理”。URL 决定发给谁，请求体决定让模型做什么，请求头决定怎么鉴权。

`base_url` 和 `endpoint` 的关系像这样：

```text
base_url:  https://api.example.com/v1
endpoint:  /chat/completions
最终 URL:  https://api.example.com/v1/chat/completions
```

两者都会打开 streaming：

```json
{
  "model": "...",
  "stream": true,
  "max_tokens": 512,
  "messages": [...]
}
```

请求体里的几个字段可以这样理解：

| 字段 | 作用 | 类比 |
|---|---|---|
| `model` | 选择要调用哪个模型 | 点哪位厨师做菜 |
| `messages` | 给模型的对话上下文 | 这次要处理的订单内容 |
| `max_tokens` | 限制最多生成多少 token | 这道菜最多做多大份 |
| `stream` | 是否边生成边返回 | 边做边端出来，而不是全部做完再端 |

鉴权也按格式区分：

```rust
if provider.api_format == "anthropic" {
    request = request
        .header("x-api-key", &provider.api_key)
        .header("anthropic-version", "2023-06-01");
} else {
    request = request.bearer_auth(&provider.api_key);
}
```

鉴权就是证明“我有权限调用这个 API”。OpenAI-compatible 通常用 `Authorization: Bearer <API_KEY>`，Anthropic-compatible 通常用 `x-api-key`。同样是 API key，不同供应商要求放在不同 header 里。

然后开始计时：

```rust
let start = Instant::now();
let response = request.send().await?;
```

如果 HTTP 状态码不是成功，就把响应文本截断后作为错误返回：

```rust
if !status.is_success() {
    let text = response.text().await.unwrap_or_default();
    return Err(format!("HTTP {status}: {}", truncate(&text, 500)));
}
```

HTTP 状态码可以理解成服务器给你的结果编号。`200` 一类通常表示成功，`401` 可能是 key 不对，`404` 可能是路径不对，`429` 可能是限流，`500` 一类通常是服务端错误。V2 不会把这些失败伪装成 0 分，而是把错误信息保存下来。

## TTFT 是怎么来的

TTFT 是 `time to first token`，也就是第一个可见 assistant 文本出现前的等待时间。

为什么不是“请求总耗时”？因为人对等待的感受分两段：

```text
第一段：什么都没出现，只能等。
第二段：已经开始输出，可以跟着读。
```

TTFT 测的是第一段。对 agent 来说，这段尤其关键，因为工具调用、规划、重试时，用户常常只能看到界面沉默。

V2 读取 streaming response：

```rust
let mut stream = response.bytes_stream();
let mut buffer = String::new();
let mut visible = String::new();
let mut ttft_ms: Option<f64> = None;
```

每收到一块 bytes，就追加到 buffer，然后按换行拆出 SSE 行：

```rust
while let Some(index) = buffer.find('\n') {
    let line = buffer[..index].trim().to_string();
    buffer = buffer[index + 1..].to_string();
    if !line.starts_with("data:") {
        continue;
    }
    ...
}
```

这里的 `buffer` 像一个临时水槽。网络数据不是按完整句子来的，而是一小块一小块来的。有时候一块数据里只有半行，所以要先放进 buffer，等凑到换行符再处理。

SSE 可以理解成一种“服务器一行一行推消息给客户端”的格式。很多 LLM streaming API 会返回类似这样的内容：

```text
data: {"choices":[{"delta":{"content":"你"}}]}
data: {"choices":[{"delta":{"content":"好"}}]}
data: [DONE]
```

每一行 `data:` 都可能包含一小段模型刚生成的文本。

遇到 `data:` 行后，调用 `extract_stream_text()` 提取 assistant 文本：

```rust
if let Some(text) = extract_stream_text(data, &provider.api_format) {
    if !text.trim().is_empty() && ttft_ms.is_none() {
        ttft_ms = Some(start.elapsed().as_secs_f64() * 1000.0);
    }
    visible.push_str(&text);
}
```

这就是 TTFT 的定义：

```text
从 request.send() 前开始计时，到第一段非空 assistant 文本出现为止。
```

如果整个 stream 都没有可见 assistant 文本，就返回失败：

```rust
let ttft_ms = ttft_ms.ok_or_else(|| "No visible streamed assistant text".to_string())?;
```

这也很重要：没有真实文本，就不算成功测速。

## 生成速度是怎么估的

V2 没有引入 tokenizer，所以用一个简单估算：

```rust
fn estimate_tokens(text: &str) -> f64 {
    let chars = text.chars().count() as f64;
    (chars / 4.0).max(1.0)
}
```

也就是大致认为 4 个字符约等于 1 个 token。这个估算不完美，但足够做跨 provider 的粗略速度对比。

Tokenizer 是“把文本切成 token 的工具”。不同模型的 tokenizer 不完全一样，如果要非常精确，就需要按具体模型加载对应 tokenizer。V2 现在选择更轻的实现：不用引入复杂依赖，用字符数估算一个足够直观的 tokens/s。

生成速度计算方式是：

```rust
let elapsed_after_ttft = (start.elapsed().as_secs_f64() - ttft_ms / 1000.0).max(0.001);
let estimated_tokens = estimate_tokens(&visible);
decode_tps = estimated_tokens / elapsed_after_ttft
```

换成人话：

```text
先扣掉等待首 token 的时间，再用后续生成出来的文本估算 tokens/s。
```

这比“总输出 token / 总耗时”更贴近体验，因为首 token 等待和后续生成速度是两种不同的慢。

## Stream 文本怎么解析

OpenAI compatible 的 streaming 常见格式是：

```json
{
  "choices": [
    {
      "delta": {
        "content": "hello"
      }
    }
  ]
}
```

Anthropic compatible 的 streaming 文本可能在：

```json
{
  "delta": {
    "text": "hello"
  }
}
```

所以 `extract_stream_text()` 做了格式分支：

```rust
if api_format == "anthropic" {
    value.get("delta").and_then(|delta| delta.get("text"))...
} else {
    value.get("choices")
        .and_then(Value::as_array)
        .and_then(|choices| choices.first())
        .and_then(|choice| choice.get("delta"))
        .and_then(|delta| delta.get("content"))...
}
```

这就是为什么 provider 配置里要选择 `OpenAI compatible` 或 `Anthropic compatible`。同样是 streaming API，但响应 JSON 的文本位置不一样。

JSON 可以理解成一种通用的数据包装格式。它像一个嵌套的快递盒：文本不一定放在第一层，可能藏在 `choices[0].delta.content`，也可能藏在 `delta.text`。`extract_stream_text()` 的工作就是打开盒子，找到真正可见的 assistant 文本。

## 数据库保存什么

SQLite 初始化在 `v2/src-tauri/src/database/mod.rs`。

数据库的抽象很简单：它是一堆表。表像 Excel，每一列有固定含义，每一行是一条记录。

```text
providers 表：记录“有哪些 API 配置”
speedtest_runs 表：记录“每次测速发生了什么”
```

启动时会创建本地数据库：

```rust
let db_path = data_dir.join("llm-speedway.db");
let connection = Connection::open(db_path)?;
```

如果拿不到 Tauri 的 app data 目录，会退回：

```text
~/.llm-speedway/llm-speedway.db
```

数据库有两张核心表：

```text
providers
speedtest_runs
```

`providers` 保存 API 配置：

- provider 名称
- base URL
- endpoint
- model
- API key
- api_format
- tags
- note

也就是说，`providers` 是“供应商档案”。用户每新增一个配置，就会多一行。

`speedtest_runs` 保存每次测速结果：

- provider 信息快照
- status
- started_at / finished_at
- ttft_ms
- decode_tps
- multi_turn_decode_tps
- success_rate
- error_message

`speedtest_runs` 是“测速流水账”。同一个 provider 可以测很多次，所以它不是覆盖旧结果，而是一条一条追加历史。

这里还有一个值得记住的设计：测速结果里保存了 provider 名称和 model 的快照。即使你之后改了 provider 配置，历史结果仍然能显示当时测的是谁。

这就是为什么它不是只保存 `provider_id`。如果历史结果只存 ID，一旦 provider 改名或删掉，老结果就很难解释了。

## Provider 配置怎么创建

Provider 是 V2 里最核心的业务对象之一。它不是模型本身，而是“怎么调用某个模型 API”的配置。

一个 provider 大概包含：

```text
供应商名字
API 地址
endpoint
模型名
API key
API 格式
标签和备注
```

它像一张联系人卡片：你要知道对方是谁、打哪个号码、用什么暗号、找哪个具体服务。

新增配置从 `App.tsx` 的表单开始：

```ts
function addProvider(formData: FormData) {
  const input: CreateProviderInput = {
    providerName,
    baseUrl,
    endpoint: defaultEndpoint(apiFormat),
    model,
    apiFormat,
    apiKey,
    tags,
    note,
  };

  createProviderMutation.mutate(input);
}
```

然后经过：

```text
createProvider(input)
  -> invoke("create_provider", { input })
  -> commands/providers.rs
  -> ProviderService::create(input)
  -> INSERT INTO providers
```

Rust 侧的结构体使用了：

```rust
#[serde(rename_all = "camelCase")]
```

这让 TypeScript 的 `providerName` 可以自动对应 Rust 的 `provider_name`。所以前端能用符合 JS 习惯的 camelCase，Rust 能用符合 Rust 习惯的 snake_case。

## 类型是怎么对上的

“类型”就是数据的形状约定。比如 `SpeedtestResult` 这个类型规定：一次测速结果必须有 `id`、`providerId`、`model`、`status`、`createdAt`，可能有 `ttftMs`、`decodeTps`、`errorMessage`。

类型的价值是让代码提前知道自己在处理什么。没有类型时，你可能写错字段名还不知道；有类型时，编辑器和编译器会提前提醒你。

前端类型在 `v2/src/types.ts`：

```ts
export type SpeedtestResult = {
  id: string;
  providerId: string;
  providerName: string;
  displayName: string;
  model: string;
  status: SpeedtestStatus;
  ttftMs?: number;
  decodeTps?: number;
  multiTurnDecodeTps?: number;
  successRate?: number;
  errorMessage?: string;
  createdAt: string;
};
```

Rust 类型在 `v2/src-tauri/src/models/speedtest.rs`：

```rust
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SpeedtestResult {
    pub id: String,
    pub provider_id: String,
    pub provider_name: String,
    pub display_name: String,
    pub model: String,
    pub status: String,
    pub ttft_ms: Option<f64>,
    pub decode_tps: Option<f64>,
    pub multi_turn_decode_tps: Option<f64>,
    pub success_rate: Option<f64>,
    pub error_message: Option<String>,
    pub created_at: String,
}
```

你可以看到字段是一一对应的，只是命名风格不同。`serde(rename_all = "camelCase")` 就是桥。

这里的桥很重要：

```text
Rust 内部字段：provider_id
传给前端 JSON：providerId
TypeScript 读取：result.providerId
```

所以我们既保留了 Rust 社区习惯，也保留了前端社区习惯，中间由序列化工具自动转换。

## 浏览器预览模式是什么

`desktop.ts` 里还有一套 browser fallback。这不是正式桌面路径，而是为了开发预览：

```ts
if (isTauriRuntime) {
  return invoke("list_providers");
}
return browserProviders;
```

浏览器模式下：

- provider 和 result 存在 JS 内存里。
- 初始数据来自 `mockData.ts`。
- 如果你真的填了 API key，也可以用浏览器 `fetch` 测一下。

但注意：浏览器请求会遇到 CORS、环境限制等问题。V2 的正式能力应该以 Tauri 桌面模式为准。

CORS 是浏览器的安全限制。它会阻止网页随便请求别的网站 API。桌面 Tauri 的 Rust 后端不走浏览器这套限制，所以更适合做真实 API benchmark。

可以把浏览器预览模式看成“展厅样机”，桌面 Tauri 模式才是“真正上路的车”。

## 一次 Speedtest 的完整链路

把前面串起来，就是这条链：

```text
用户点击某个 provider 的 Speedtest
        |
        v
App.tsx / handleRunSpeedtest()
        |
        v
runSpeedtestMutation.mutate(provider.id)
        |
        v
desktop.ts / runSpeedtest(providerId)
        |
        v
invoke("run_speedtest", { providerId })
        |
        v
commands/speedtests.rs / run_speedtest()
        |
        v
SpeedtestService::run(providerId)
        |
        +--> load_provider()
        |
        +--> measure_provider()
        |       |
        |       +--> short request: TTFT
        |       +--> long request: decode TPS
        |       +--> multi-turn request: multi-turn TPS
        |
        +--> save_result()
        |
        v
返回 SpeedtestResult 给前端
        |
        v
React 更新结果面板
```

如果你能讲清楚这条链路，就已经看懂 V2 的核心了。

这条链路背后的分工也可以再简化成三句话：

```text
React 问：用户要测哪个 provider？
Rust 做：拿配置，发请求，算指标，存结果。
React 再问：结果是什么？然后展示出来。
```

## 现在实现的边界

读代码时，也要知道现在版本还没做什么：

- 没有真实的后端任务队列；一次测速就是一次前端 invoke 等待 Rust 返回。
- 没有实时从 Rust 推送进度；进度阶段是前端本地模拟推进。
- 没有精确 tokenizer；tokens/s 用字符数除以 4 估算。
- API key 字段名叫 `api_key_cipher`，但当前实现是直接存入 SQLite，并没有真正加密。
- `duplicate_provider()` 目前用的是 `api_key_preview`，不是原始 API key，因此复制出来的配置不能直接等价复用。

这些不是理解主链路的障碍，但它们是后续改进时很好的切入点。

边界不是坏事。一个项目好不好理解，很大程度上取决于它有没有把“现在已经做了什么”和“以后可以继续做什么”分清楚。V2 的核心已经成立：本地配置、真实 streaming 测速、本地结果保存。剩下的是准确性、安全性、任务调度和在线化。

## 推荐读代码练习

如果你想真的掌握它，可以按这几个小任务读：

1. 找到 `Speedtest` 按钮点击后调用了哪个函数。
2. 找到 `run_speedtest` 这个字符串在哪里从 TypeScript 跨到 Rust。
3. 找到首 token 延迟第一次被赋值的位置。
4. 找到测速失败时错误信息怎么保存进数据库。
5. 找到 `providers` 和 `speedtest_runs` 两张表在哪里创建。
6. 试着解释 `ProviderConfig` 为什么在 TypeScript 和 Rust 里字段名不一样但还能互通。

## 如果以后要做 V3

V2 的价值是把单机 benchmark 链路打通。V3 如果要做在线测速、多供应商实时监控报警、快速切换工具，可以沿着这条路线演进：

```text
V2 本地单次测速
        |
        v
V3 在线定时测速任务
        |
        v
多地区 / 多供应商 / 多模型结果入库
        |
        v
实时性能面板 + 异常报警
        |
        v
API 路由和快速切换工具
```

到那时，V2 里的 `SpeedtestService::measure_request()` 仍然是核心资产：它已经定义了怎么发 streaming 请求、怎么抓 TTFT、怎么估算吞吐。V3 要做的是把“本地点击一次”升级成“云端持续运行、持续记录、持续提醒”。
