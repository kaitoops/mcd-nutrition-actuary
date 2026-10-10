"""端到端演示：减脂党场景（40 元内、≤600 kcal、蛋白 ≥25g）。

运行方式（仓库根目录）：
    python examples/run_demo.py
数据来自 tests/test_optimizer.py 中的 MCP 实测快照（深圳同方信息港店）。
"""
import io
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_optimizer import MEAL_DETAIL_RAW, _role_menu
from src.models import Constraints
from src.optimizer import NutritionActuary, build_meal_details, format_report


def main():
    cons = Constraints(budget=40, max_kcal=600, min_protein=25,
                       preference="weight_loss")
    actuary = NutritionActuary(_role_menu())
    details = build_meal_details(MEAL_DETAIL_RAW, {"9900005466": 36.5})
    sols = actuary.plan(cons, details, top_k=3)
    report = format_report(sols, cons, actuary.matcher)

    # 直接以 UTF-8 写文件，绕开 Windows shell 的 GBK 编码转换
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "demo-output.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report + "\n")
    print(report)
    print(f"\n[已存档] {out_path}")


if __name__ == "__main__":
    main()
