"""精算 CLI：把 MCP 取数结果（JSON 文件）喂给优化器，输出 markdown 精算报告。

用法（仓库根目录）：
    python scripts/actuary_cli.py --constraints cons.json --menu menu.json \
        [--meal-details details.json] [--out report.md]

输入文件格式：
    cons.json     {"budget":40, "max_kcal":600, "min_protein":25,
                   "max_sodium":null, "blacklist":["香菜"], "preference":"weight_loss"}
    menu.json     [{"code":"1100","name":"巨无霸","price":25.5,"category":"..."}, ...]
                  （query-meals 的 categories[].meals[].code + meals.{code} 展平）
    details.json  query-meal-detail 返回的 data 数组原样（可选，最多 5 个套餐）
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.matcher import NutritionMatcher
from src.models import Constraints, MenuItem
from src.optimizer import NutritionActuary, build_meal_details, categorize, format_report


def load_menu(raw):
    items = []
    for m in raw:
        role = categorize(m.get("name", "")) or ""
        items.append(MenuItem(
            code=str(m.get("code", "")),
            name=m.get("name", ""),
            price=float(m.get("price", 0)),
            category=m.get("category", ""),
            role=role,
        ))
    return items


def main():
    ap = argparse.ArgumentParser(description="麦麦营养精算师 CLI")
    ap.add_argument("--constraints", required=True)
    ap.add_argument("--menu", required=True)
    ap.add_argument("--meal-details", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--top-k", type=int, default=3)
    args = ap.parse_args()

    with open(args.constraints, encoding="utf-8") as f:
        c = json.load(f)
    cons = Constraints(
        budget=float(c.get("budget", 50)),
        max_kcal=c.get("max_kcal"),
        min_protein=c.get("min_protein"),
        max_sodium=c.get("max_sodium"),
        blacklist=c.get("blacklist", []),
        preference=c.get("preference", "balanced"),
    )

    with open(args.menu, encoding="utf-8") as f:
        menu = load_menu(json.load(f))

    details = None
    prices = {m.code: m.price for m in menu}
    if args.meal_details and os.path.exists(args.meal_details):
        with open(args.meal_details, encoding="utf-8") as f:
            details = build_meal_details(json.load(f), prices)

    actuary = NutritionActuary(menu)
    sols = actuary.plan(cons, details, top_k=args.top_k)
    report = format_report(sols, cons, actuary.matcher)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"[已写出] {args.out}")
    print(report)
    if not sols:
        print("\n[!] 无可行解：建议放宽预算/热量/蛋白约束后再试。", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
