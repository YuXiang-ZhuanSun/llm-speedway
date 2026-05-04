import json
import tempfile
import unittest
from pathlib import Path

from llm_speedway.scenarios.loader import load_scenarios, parse_scenario


class ScenarioLoaderTests(unittest.TestCase):
    """外部 JSON 用例加载器测试。"""

    def test_parse_valid_single_turn_scenario(self):
        # 直接从 dict 解析，覆盖最小可用 single_turn 用例。
        scenario = parse_scenario(
            {
                "name": "demo",
                "description": "demo case",
                "kind": "single_turn",
                "prompts": ["Hello"],
                "max_tokens": 32,
            }
        )
        self.assertEqual(scenario.name, "demo")
        self.assertEqual(scenario.max_tokens, 32)

    def test_load_scenario_from_directory(self):
        # 模拟用户在自定义 scenarios_dir 中新增用例文件。
        with tempfile.TemporaryDirectory() as temp_dir:
            scenario_path = Path(temp_dir) / "custom.json"
            scenario_path.write_text(
                json.dumps(
                    {
                        "name": "custom",
                        "description": "custom case",
                        "kind": "multi_turn",
                        "prompts": ["first", "second"],
                    }
                ),
                encoding="utf-8",
            )
            scenarios = load_scenarios(["custom"], temp_dir)
            self.assertEqual(len(scenarios), 1)
            self.assertEqual(scenarios[0].kind, "multi_turn")

    def test_rejects_invalid_kind(self):
        # kind 只能是 single_turn 或 multi_turn，避免运行时才发现配置错误。
        with self.assertRaises(ValueError):
            parse_scenario({"name": "bad", "kind": "other", "prompts": ["Hello"]})


if __name__ == "__main__":
    unittest.main()
