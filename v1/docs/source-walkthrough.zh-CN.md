# llm-speedway 源码解读

这篇文档按一次真实的 `llm-speedway run` 调用顺序解读源码。读完后，你应该能从命令行入口一路追到请求发送、streaming 解析、指标计算和报告输出。

## 1. 命令行入口

调用从 `llm_speedway/cli.py` 开始。

### `build_parser()`

`build_parser()` 负责定义命令行参数。项目目前只有一个核心子命令：

```powershell
llm-speedway run --config config.json
```

它支持这些运行时覆盖项：

- `--config`：指定配置文件，默认读取 `config.json`
- `--scenario`：指定要跑的场景，可以传多次
- `--runs`：覆盖 `benchmark.runs_per_scenario`
- `--results-dir`：覆盖 `benchmark.results_dir`

CLI 层只解析参数，不做 HTTP 请求、不算指标、也不写报告。

### `main(argv=None)`

`main()` 是命令执行的总入口。它的调用顺序是：

1. 调用 `build_parser()` 构建解析器。
2. 用 `parser.parse_args(argv)` 解析命令行参数。
3. 如果不是 `run` 命令，就打印帮助并退出。
4. 调用 `load_config(Path(args.config))` 读取配置文件。
5. 把命令行参数覆盖到配置对象上。
6. 创建 `BenchmarkRunner(config)`。
7. 调用 `runner.run()` 执行 benchmark。
8. 打印最终报告路径。

异常处理也集中在这里：`KeyboardInterrupt` 返回 `130`，其他异常返回 `1`，这样对 shell 和 CI 都比较友好。

### `llm_speedway/__main__.py`

`__main__.py` 让项目支持另一种启动方式：

```powershell
python -m llm_speedway
```

它只做一件事：导入并调用 `cli.main()`。

## 2. 配置加载

配置逻辑在 `llm_speedway/core/config.py`。

### 配置 dataclass

配置文件会被转换成几个强类型对象：

- `ApiConfig`：保存 `base_url`、`api_key`、`model`、`endpoint`
- `BenchmarkConfig`：保存运行次数、超时、预热次数、结果目录、场景目录等
- `GenerationConfig`：保存 `temperature`、`max_tokens`、`top_p`
- `AppConfig`：把上面三类配置组合起来，并保存要运行的场景列表

这样 runner 后续不需要到处读取原始 `dict`，也减少了字符串 key 写错的风险。

### `load_config(path)`

`load_config()` 是配置入口函数：

1. 检查配置文件是否存在。
2. 调用 `_load_raw_config(path)` 读取 JSON 或 YAML。
3. 调用 `parse_config(raw)` 转成 `AppConfig`。

如果配置文件不存在，会直接抛出 `FileNotFoundError`。

### `_load_raw_config(path)`

`_load_raw_config()` 根据文件后缀选择解析方式：

- `.json`：用标准库 `json.loads()`
- `.yaml` / `.yml`：尝试导入 `PyYAML` 后用 `yaml.safe_load()`

如果 YAML 没安装，会给出明确错误；如果后缀不是支持格式，会抛出 `ValueError`。

### `parse_config(raw)`

`parse_config()` 把原始配置转换成最终的 `AppConfig`。它主要做四件事：

1. 校验 `api.base_url`、API key、`api.model` 这些必填项。
2. 调用 `_resolve_api_key(api_raw)` 解析 API key。
3. 给 benchmark 和 generation 字段填默认值。
4. 调用 `_normalize_endpoint()` 规范化接口路径。

这里也会把 `base_url` 末尾的 `/` 去掉，避免后面拼接 endpoint 时出现双斜杠。

### `_resolve_api_key(api_raw)`

API key 有两种来源：

- 直接写在 `api.api_key`
- 通过 `api.api_key_env` 指定环境变量名，再从环境变量读取

函数优先使用明文 `api_key`。如果没有，就读取环境变量。两者都没有时返回空字符串，随后由 `parse_config()` 抛出配置错误。

### `_normalize_endpoint(endpoint)`

这个函数保证 endpoint 一定以 `/` 开头。比如用户写 `chat/completions`，会被规范化为 `/chat/completions`。

### `_optional_float(value)`

用于解析 `top_p` 这类可选浮点数。传入 `None` 时返回 `None`，否则转成 `float`。

## 3. Runner 编排

核心编排逻辑在 `llm_speedway/runner.py`。

### `BenchmarkRunner.__init__(config)`

构造函数保存完整配置，并创建 OpenAI-compatible provider：

```python
self.client = OpenAICompatibleClient(config.api, config.benchmark.timeout_seconds)
```

Runner 不关心底层 HTTP 细节，只通过 `self.client.complete()` 发起模型调用。

### `BenchmarkRunner.run()`

`run()` 是 benchmark 主流程。它的执行顺序是：

1. 调用 `load_scenarios()` 按配置加载场景。
2. 创建空的 `records` 列表，用来保存每次请求的原始记录。
3. 遍历每个场景。
4. 先调用 `_run_warmups(scenario)` 执行预热。
5. 按 `runs_per_scenario` 执行正式请求。
6. 如果场景是 `multi_turn`，调用 `_run_multi_turn()`。
7. 否则调用 `_run_single_turn()`。
8. 调用 `summarize(records)` 聚合结果。
9. 创建 `Reporter(results_dir)`。
10. 调用 `reporter.write_all()` 写出报告、CSV 和 JSONL。

它把“场景 -> 请求 -> 指标 -> 报告”串起来，但不直接处理每一层的实现细节。

### `_run_warmups(scenario)`

预热请求用于降低冷启动、连接建立等噪声。它会根据场景类型调用：

- `_run_multi_turn(scenario, run_id=-warmup_id)`
- `_run_single_turn(scenario, run_id=-warmup_id, round_id=None)`

注意预热结果不会加入正式 `records`，因为 `_run_warmups()` 不返回记录。预热失败也只打印错误，不中断正式 benchmark。

### `_run_single_turn(scenario, run_id, round_id)`

单轮场景只取 `scenario.prompts[0]`，组装成 Chat Completions 需要的 messages：

```python
messages = [{"role": "user", "content": scenario.prompts[0]}]
```

然后把请求交给 `_execute_request()`。

### `_run_multi_turn(scenario, run_id)`

多轮场景会逐轮累积上下文。每一轮的流程是：

1. 把当前 prompt 作为 `user` message 加入 `messages`。
2. 调用 `_execute_request()` 发起请求。
3. 把返回的 `RequestRecord` 放入本轮 records。
4. 如果请求成功，并且有 assistant 内容，就把 assistant 回复加入 `messages`。
5. 如果请求失败，就停止后续轮次。

这让第 2 轮请求携带第 1 轮 assistant 回复，第 3 轮携带前两轮上下文，从而模拟真实 agent 对话越来越重的情况。

### `_execute_request(scenario, run_id, round_id, messages)`

这是单次 API 请求的封装点，也是 runner 和 provider、metrics 的交汇处。

成功路径如下：

1. 记录 `created_at`。
2. 调用 `self.client.complete()` 发起模型请求。
3. 检查 `result.content.strip()`，空可见回复会被视为失败。
4. 优先读取 provider 返回的 `output_tokens` 和 `input_tokens`。
5. 如果 provider 没返回 usage，就调用本地 token 估算函数。
6. 调用 `calculate_speed_metrics()` 计算速度指标。
7. 构造并返回成功的 `RequestRecord`。

失败路径会捕获异常并返回失败的 `RequestRecord`。失败记录仍然保留 `scenario`、`run_id`、`round_id`、`model`、`created_at` 和估算输入 token，方便报告展示成功率和错误原因。

## 4. 场景加载

场景加载逻辑在 `llm_speedway/scenarios/loader.py`。真实场景文件放在项目根目录的 `scenarios/` 下。

### `Scenario`

`Scenario` 是一个冻结 dataclass，字段包括：

- `name`：场景名
- `description`：场景说明
- `kind`：只能是 `single_turn` 或 `multi_turn`
- `prompts`：用户 prompt 列表
- `max_tokens`：可选的场景级输出长度上限

### `load_scenarios(names, scenarios_dir="scenarios")`

这个函数按配置顺序加载多个场景。它会遍历 `names`，并对每个名字调用 `load_scenario(name, root)`。

### `load_scenario(name_or_path, scenarios_dir)`

加载单个场景的流程是：

1. 调用 `_resolve_scenario_path()` 把场景名解析成 JSON 路径。
2. 如果文件不存在，调用 `_available_scenarios()` 生成错误提示。
3. 读取 JSON。
4. 确认 JSON 根节点是对象。
5. 调用 `parse_scenario(raw, source=path)` 转成 `Scenario`。

### `parse_scenario(raw, source=None)`

这个函数负责字段校验：

- `name` 必须存在
- `kind` 必须是 `single_turn` 或 `multi_turn`
- `prompts` 必须是非空字符串列表
- `max_tokens` 如果存在，会转成 `int`

校验通过后返回 `Scenario`。

### `_resolve_scenario_path(name_or_path, scenarios_dir)`

如果传入的是 JSON 路径或带目录的路径，就直接使用该路径。否则把场景名解析为：

```text
scenarios/<name>.json
```

比如 `short_chat` 会解析为 `scenarios/short_chat.json`。

### `_available_scenarios(scenarios_dir)`

这个函数扫描场景目录下的 `*.json`，返回可用场景名列表。主要用于未知场景时给出更友好的错误消息。

## 5. Provider 请求执行

OpenAI-compatible 适配器在 `llm_speedway/providers/openai_compatible.py`。

### `CompletionResult`

`CompletionResult` 表示一次模型调用的原始结果，包括：

- `content`：完整 assistant 文本
- `ttft_ms`：首个可见 token 到达时间
- `total_latency_ms`：请求总耗时
- `input_tokens` / `output_tokens`：provider usage 中的 token 数
- `finish_reason`：模型停止原因
- `raw_usage`：完整 usage 对象

### `OpenAICompatibleClient.__init__(api, timeout_seconds)`

构造函数只保存 API 配置和超时时间。

### `complete(messages, generation, stream=True, max_tokens_override=None)`

`complete()` 会把上游配置转换成 Chat Completions payload：

- `model`
- `messages`
- `temperature`
- `max_tokens`
- `stream`
- 可选的 `top_p`

如果场景设置了 `max_tokens`，会优先使用场景级 `max_tokens_override`；否则使用全局 `generation.max_tokens`。

当 `stream=True` 时，payload 会加上：

```python
"stream_options": {"include_usage": True}
```

这样支持该选项的 provider 可以在 stream 里返回 usage。随后函数创建 `urllib.request.Request`，根据 `stream` 选择：

- `_complete_streaming(request)`
- `_complete_non_streaming(request)`

### `_complete_streaming(request)`

这是 TTFT 指标最关键的函数。它处理 Server-Sent Events 风格的 streaming 响应：

1. 用 `time.perf_counter()` 记录请求开始时间。
2. 初始化 `first_token_at`、`chunks`、`usage`、`finish_reason`。
3. 调用 `urllib.request.urlopen()` 发起请求。
4. 逐行读取响应。
5. 忽略空行和非 `data:` 行。
6. 遇到 `data: [DONE]` 时结束。
7. 解析每个 JSON event。
8. 如果 event 带 `usage`，保存 usage。
9. 遍历 `choices`，读取 `delta.content`。
10. 第一次读到可见 content 时记录 `first_token_at`。
11. 把每个 content 片段追加到 `chunks`。
12. 请求结束后计算总耗时。
13. 返回 `CompletionResult`。

这里的 TTFT 不是“HTTP 建连成功时间”，而是“第一次出现可见 assistant 文本的时间”。这更接近用户感受到的等待时间。

HTTP 错误会被包装成 `RuntimeError(f"HTTP {code}: {body}")`；网络错误会被包装成 `RuntimeError(f"Request failed: {reason}")`。

### `_complete_non_streaming(request)`

非 streaming 模式无法观测首 token，所以返回的 `ttft_ms` 是 `None`。它的流程是：

1. 记录开始时间。
2. 一次性读取完整响应 body。
3. 解析 JSON。
4. 读取第一个 choice 的 `message.content`。
5. 读取 usage 和 `finish_reason`。
6. 返回 `CompletionResult`。

这个模式仍然能得到总耗时和端到端 TPS，但不能得到真实 TTFT 和 decode TPS。

### `_usage_int(usage, key)`

从 provider usage 对象里安全读取整数 token 字段。usage 不存在或字段为空时返回 `None`。

## 6. Token 估算

fallback token 估算在 `llm_speedway/core/token_counter.py`。

### `estimate_tokens(text)`

当 provider 没有返回 usage 时，项目用这个函数粗略估算输出 token 数。

它会：

1. 用 `_CJK_RE` 统计中文、日文、韩文等 CJK 字符数量。
2. 把 CJK 字符替换成空格。
3. 用 `_WORD_OR_SYMBOL_RE` 统计英文单词、数字、下划线片段和符号。
4. 返回两者之和，空文本返回 `0`。

这是为了 benchmark 的相对比较，不是账单级 token 统计。

### `estimate_messages_tokens(messages)`

这个函数估算输入 messages 的 token 数：

```python
content_tokens + len(messages) * 4
```

其中 `len(messages) * 4` 是对 chat message 结构开销的轻量估计。

## 7. 指标计算与聚合

指标逻辑在 `llm_speedway/core/metrics.py`。

### `RequestRecord`

`RequestRecord` 是每次请求的原始记录。它同时服务三件事：

- 给 summary 聚合提供数据
- 写入 `raw_results.jsonl`
- 在多轮场景里保存 `assistant_content`，供下一轮上下文使用

字段包括场景名、运行编号、轮次、模型、成功状态、token 数、TTFT、总耗时、decode TPS、端到端 TPS、错误信息和内容预览等。

### `RequestRecord.to_dict()`

写 JSONL 时调用。它会：

- 输出公开可读的字段
- 调用 `_round_or_none()` 统一把浮点数保留三位小数
- 不输出完整 `assistant_content`

完整 assistant 内容可能很长，也只需要在运行时传给下一轮，不适合写进公开报告。

### `calculate_speed_metrics(ttft_ms, total_latency_ms, output_tokens)`

这个函数计算三个速度相关值：

- `generation_time_ms`：`total_latency_ms - ttft_ms`
- `decode_tps`：`output_tokens / generation_time_seconds`
- `end_to_end_tps`：`output_tokens / total_latency_seconds`

如果没有 `ttft_ms`，就无法计算 `generation_time_ms` 和 `decode_tps`。但只要 `total_latency_ms > 0`，仍然可以计算端到端 TPS。

### `summarize(records)`

`summarize()` 把所有请求记录按 `(scenario, round_id)` 分组。每组都会输出：

- `runs`
- `successes`
- `success_rate`
- 各指标的平均值、p50、p90、p95、最小值、最大值

只有成功记录参与数值统计，但失败记录会计入总运行次数，所以成功率不会被高估。

### `_stats(prefix, values)`

对某个指标的一组数值计算统计量：

- 平均值
- p50
- p90
- p95
- min
- max

如果没有可用值，就为这些字段全部返回 `None`。

### `_percentile(sorted_values, percentile)`

用线性插值计算分位数。只有一个值时，直接返回这个值。

### `_round_or_none(value)`

统一处理 JSONL 中的浮点数展示：`None` 保持为 `None`，数字保留三位小数。

## 8. 报告输出

报告逻辑在 `llm_speedway/reports/markdown.py`。

### `Reporter.__init__(results_dir)`

保存结果目录，并确保目录存在：

```python
self.results_dir.mkdir(parents=True, exist_ok=True)
```

### `write_all(config, records, summary_rows)`

一次性写出三类产物：

1. `_write_raw(records)` 写 `raw_results.jsonl`
2. `_write_summary_csv(summary_rows)` 写 `summary.csv`
3. `_write_markdown(config, summary_rows, records)` 写 `report.md`

最终返回 Markdown 报告路径。

### `_write_raw(records)`

把每个 `RequestRecord` 调用 `to_dict()` 后写成一行 JSON。这个文件最适合用于排查问题和复现实验。

### `_write_summary_csv(summary_rows)`

写面向表格工具的简洁 CSV。目前输出字段是：

- `scenario`
- `round_id`
- `runs`
- `success_rate`
- `ttft_ms_avg`
- `total_latency_ms_avg`
- `decode_tps_avg`

如果没有 summary 数据，就写一个空文件。

### `_write_markdown(config, summary_rows, records)`

生成给人读的 `report.md`。它会包含：

- 模型名和 API base URL
- 每个场景的运行次数和整体成功率
- `_headline(summary_rows)` 生成的一句话摘要
- 核心速度指标表
- 指标解释
- 最多 20 条错误记录

报告刻意只突出 Start latency 和 Generation speed，避免把原始指标全部堆给读者。

### `_headline(summary_rows)`

生成报告开头的一句话摘要。它会尝试读取：

- `short_chat` 的平均 TTFT
- `long_generation` 的平均 decode TPS
- 最后一轮成功的 `multi_turn` decode TPS

如果没有任何成功样本，就返回 `No successful samples were collected.`

### `_find_row(summary_rows, scenario, round_id)`

在 summary 里查找指定场景和轮次的聚合行。

### `_fmt_ms(value)`

把毫秒转成秒展示，例如 `6330` 会显示成 `6.33s`。空值显示 `-`。

### `_fmt_tps(value)`

把 TPS 格式化成 `xx.x tok/s`。空值显示 `-`。

## 9. 一次完整调用链

把上面的函数串起来，一次 `llm-speedway run` 的主路径是：

```text
llm_speedway.__main__
  -> cli.main()
    -> build_parser()
    -> load_config()
      -> _load_raw_config()
      -> parse_config()
        -> _resolve_api_key()
        -> _normalize_endpoint()
    -> BenchmarkRunner(config)
      -> OpenAICompatibleClient(api, timeout)
    -> BenchmarkRunner.run()
      -> load_scenarios()
        -> load_scenario()
          -> _resolve_scenario_path()
          -> parse_scenario()
      -> _run_warmups()
      -> _run_single_turn() / _run_multi_turn()
        -> _execute_request()
          -> OpenAICompatibleClient.complete()
            -> _complete_streaming() / _complete_non_streaming()
              -> _usage_int()
          -> estimate_tokens() / estimate_messages_tokens()
          -> calculate_speed_metrics()
          -> RequestRecord(...)
      -> summarize()
        -> _stats()
          -> _percentile()
      -> Reporter.write_all()
        -> _write_raw()
          -> RequestRecord.to_dict()
            -> _round_or_none()
        -> _write_summary_csv()
        -> _write_markdown()
          -> _headline()
          -> _find_row()
          -> _fmt_ms()
          -> _fmt_tps()
```

这条链路也体现了项目的边界划分：CLI 负责入口，config 负责配置，scenarios 负责用例，provider 负责协议，metrics 负责计算，reporter 负责输出，runner 负责把它们编排成一次完整 benchmark。
