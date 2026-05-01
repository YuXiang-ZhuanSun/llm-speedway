import unittest

from llm_speedway.core.metrics import RequestRecord
from llm_speedway.core.metrics import calculate_speed_metrics, summarize


class MetricsTests(unittest.TestCase):
    """指标计算与聚合逻辑测试。"""

    def test_calculate_speed_metrics(self):
        # 总耗时 2500ms，首 token 500ms，说明持续生成阶段是 2000ms。
        generation_ms, decode_tps, e2e_tps = calculate_speed_metrics(500, 2500, 100)
        self.assertEqual(generation_ms, 2000)
        self.assertEqual(decode_tps, 50)
        self.assertEqual(e2e_tps, 40)

    def test_summarize_success_rate(self):
        # 只有成功样本参与数值统计，但成功率要包含失败样本。
        records = [
            RequestRecord("short", 1, None, "m", True, 10, 20, 100, 1000, 900, 22.2, 20, "stop", None, "now"),
            RequestRecord("short", 2, None, "m", False, 10, None, None, None, None, None, None, None, "err", "now"),
        ]
        rows = summarize(records)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["success_rate"], 0.5)
        self.assertEqual(rows[0]["ttft_ms_avg"], 100)

    def test_summarize_keeps_empty_groups(self):
        # 全失败场景仍要出现在 summary 里，报告才能展示失败状态。
        records = [
            RequestRecord("multi", 1, 1, "m", False, 10, None, None, None, None, None, None, None, "err", "now"),
        ]
        rows = summarize(records)
        self.assertEqual(rows[0]["success_rate"], 0)
        self.assertIsNone(rows[0]["ttft_ms_avg"])


if __name__ == "__main__":
    unittest.main()
