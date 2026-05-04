# Scenarios

这个目录存放 benchmark 用例。每个用例是一个独立 JSON 文件，文件名就是 config 里引用的场景名。

最小结构：

```json
{
  "name": "my_case",
  "description": "这个用例想观察什么。",
  "kind": "single_turn",
  "max_tokens": 512,
  "prompts": ["你的测试 prompt"]
}
```

字段说明：

| Field | Required | Meaning |
|---|---:|---|
| `name` | yes | 场景名，建议与文件名一致 |
| `description` | no | 人类可读的场景说明 |
| `kind` | yes | `single_turn` 或 `multi_turn` |
| `max_tokens` | no | 场景级输出上限，会覆盖全局 generation.max_tokens |
| `prompts` | yes | prompt 列表；多轮场景会按顺序逐轮执行 |

新增用例后，在配置文件里引用：

```json
{
  "benchmark": {
    "scenarios_dir": "scenarios"
  },
  "scenarios": ["my_case"]
}
```

