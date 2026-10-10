"""麦麦营养精算师 · 核心算法单元测试（零依赖，python -m unittest）。

测试数据全部来自 2026-10-10 麦当劳中国 MCP 实测（深圳同方信息港店 storeCode=1420762）。
"""
import unittest

from src.matcher import NutritionMatcher, normalize
from src.models import Choice, ComboRound, Constraints, MealDetail, MenuItem, Nutrition
from src.optimizer import (
    NutritionActuary, build_meal_details, categorize, format_report,
    parse_diff_price,
)

# ---- 实测菜单子集（code 来自 MCP query-meals，价格为元）----
MENU = [
    MenuItem("1100", "巨无霸", 25.5, "巨无霸\n牛鱼肉堡"),
    MenuItem("1406", "板烧鸡腿堡", 23.5, "鸡肉汉堡\n/卷"),
    MenuItem("1440", "麦辣鸡腿汉堡", 22.5, "鸡肉汉堡\n/卷"),
    MenuItem("1450", "麦香鸡", 17.0, "鸡肉汉堡\n/卷"),
    MenuItem("1600", "麦香鱼", 22.5, "巨无霸\n牛鱼肉堡"),
    MenuItem("1120", "双层吉士汉堡", 23.0, "巨无霸\n牛鱼肉堡"),
    MenuItem("4648", "不素之霸双层牛堡", 26.5, "巨无霸\n牛鱼肉堡"),
    MenuItem("1106", "培根蔬萃双层牛堡", 24.5, "巨无霸\n牛鱼肉堡"),
    MenuItem("521816", "酥酥多笋卷", 20.5, "鸡肉汉堡\n/卷"),
    MenuItem("1401", "麦乐鸡", 14.0, "炸鸡"),
    MenuItem("1700", "麦辣鸡翅", 15.0, "炸鸡"),
    MenuItem("520445", "薄皮焦香V翅", 16.0, "炸鸡"),
    MenuItem("521156", "那么大鸡排", 14.0, "炸鸡"),
    MenuItem("4810", "薯条", 13.5, "小食甜品\n/其他"),
    MenuItem("4437", "玉米杯", 13.0, "小食甜品\n/其他"),
    MenuItem("6102", "苹果片", 7.0, "小食甜品\n/其他"),
    MenuItem("9900008751", "可乐", 9.5, "饮品"),
    MenuItem("3010", "雪碧", 9.5, "饮品"),
    MenuItem("515280", "阳光柠檬红茶", 9.5, "饮品"),
    MenuItem("515520", "怡泉+C", 11.5, "饮品"),
    MenuItem("3755", "纯牛奶(盒装)", 10.5, "饮品"),
    MenuItem("6362", "100% 苹果汁(盒装)", 11.5, "饮品"),
    MenuItem("520689", "鲜萃咖啡", 9.5, "麦咖啡™"),
    MenuItem("3505", "锡兰红茶", 11.5, "饮品"),
    MenuItem("507411", "麦咖啡™美式", 11.9, "麦咖啡™"),
    MenuItem("515837", "圆筒冰淇淋", 5.0, "小食甜品\n/其他"),
]


def _role_menu():
    """给菜单打角色标签（模拟 Skill 层用 categorize() 预处理后的输入）。"""
    for m in MENU:
        m.role = categorize(m.name) or ""
    return MENU


# ---- 实测套餐详情（巨无霸三件套，storeCode=1420762）----
MEAL_DETAIL_RAW = [{
    "code": "9900005466",
    "name": "巨无霸三件套",
    "rounds": [
        {"name": "新升级巨无霸", "choices": [
            {"code": "1100", "name": "巨无霸", "isDefault": 1, "diffPrice": "+ ¥0"},
        ]},
        {"name": "选择套餐内小食", "choices": [
            {"code": "4810", "name": "中薯条", "isDefault": 1, "diffPrice": "+ ¥0"},
            {"code": "4437", "name": "小杯玉米杯", "isDefault": 0, "diffPrice": "- ¥0.5"},
            {"code": "4820", "name": "大薯条", "isDefault": 0, "diffPrice": "+ ¥2.5"},
        ]},
        {"name": "选择套餐内饮料", "choices": [
            {"code": "3050", "name": "可乐中杯", "isDefault": 1, "diffPrice": "+ ¥0"},
            {"code": "3071", "name": "无糖可口可乐中杯", "isDefault": 0, "diffPrice": "+ ¥0"},
            {"code": "3060", "name": "雪碧中杯", "isDefault": 0, "diffPrice": "+ ¥0"},
            {"code": "3505", "name": "锡兰红茶", "isDefault": 0, "diffPrice": "+ ¥1.5"},
            {"code": "3755", "name": "纯牛奶", "isDefault": 0, "diffPrice": "+ ¥0.5"},
        ]},
    ],
}]


class TestParseDiffPrice(unittest.TestCase):
    def test_plus(self):
        self.assertEqual(parse_diff_price("+ ¥1"), 1.0)

    def test_minus_decimal(self):
        self.assertEqual(parse_diff_price("- ¥0.5"), -0.5)

    def test_zero_and_garbage(self):
        self.assertEqual(parse_diff_price("+ ¥0"), 0.0)
        self.assertEqual(parse_diff_price(""), 0.0)
        self.assertEqual(parse_diff_price("n/a"), 0.0)


class TestCategorize(unittest.TestCase):
    def test_roles(self):
        self.assertEqual(categorize("巨无霸"), "main")
        self.assertEqual(categorize("板烧鸡腿堡"), "main")
        self.assertEqual(categorize("麦香鱼"), "main")
        self.assertEqual(categorize("那么大鸡排"), "main")
        self.assertEqual(categorize("薯条"), "side")
        self.assertEqual(categorize("小杯玉米杯"), "side")
        self.assertEqual(categorize("苹果片"), "side")
        self.assertEqual(categorize("无糖可口可乐中杯"), "drink")
        self.assertEqual(categorize("麦咖啡™美式"), "drink")
        self.assertEqual(categorize("纯牛奶(盒装)"), "drink")
        self.assertIsNone(categorize("如意百宝袋"))


class TestMatcher(unittest.TestCase):
    def setUp(self):
        self.m = NutritionMatcher()

    def test_alias_and_decoration(self):
        self.assertIsNotNone(self.m.match("麦咖啡™美式"))
        # 冰美式实测 kcal=13（54 是 kJ）——黑咖啡本来就没热量
        self.assertAlmostEqual(self.m.match("麦咖啡™美式").kcal, 13, delta=1)

    def test_exact(self):
        self.assertAlmostEqual(self.m.match("巨无霸").kcal, 513, delta=1)
        self.assertAlmostEqual(self.m.match("无糖可口可乐中杯").kcal, 0, delta=1)

    def test_bracket_normalization(self):
        # 菜单"纯牛奶(盒装)"半角 vs 营养表"纯牛奶（盒装）"全角
        self.assertIsNotNone(self.m.match("纯牛奶(盒装)"))

    def test_substring_short_name(self):
        # 菜单"薯条"应匹配中薯条（长度差最小）
        self.assertAlmostEqual(self.m.match("薯条").kcal, 289, delta=1)
        self.assertAlmostEqual(self.m.match("玉米杯").kcal, 53, delta=1)

    def test_unmatched_returns_none(self):
        self.assertIsNone(self.m.match("麦当劳联名复古棒球帽"))


class TestOptimizerPersonas(unittest.TestCase):
    """三个人设用例：减脂党 / 增肌党 / 省钱党。"""

    def setUp(self):
        self.actuary = NutritionActuary(_role_menu())
        self.details = build_meal_details(
            MEAL_DETAIL_RAW, {"9900005466": 36.5})

    def test_weight_loss_persona(self):
        """减脂党：40 元内、≤600 kcal、蛋白 ≥25g。"""
        cons = Constraints(budget=40, max_kcal=600, min_protein=25,
                           preference="weight_loss")
        sols = self.actuary.plan(cons, self.details)
        self.assertGreater(len(sols), 0, "减脂场景应有可行解")
        for s in sols:
            self.assertLessEqual(s.price, 40)
            self.assertLessEqual(s.nutrition.kcal, 600)
            self.assertGreaterEqual(s.nutrition.protein, 25)
        # Top1 应优于"巨无霸默认套餐"这类高热量选择
        self.assertLessEqual(sols[0].nutrition.kcal, 600)
        report = format_report(sols, cons, self.actuary.matcher)
        self.assertIn("精算报告", report)
        self.assertIn("km", report)

    def test_muscle_gain_persona(self):
        """增肌党：50 元内、蛋白 ≥40g。"""
        cons = Constraints(budget=50, min_protein=40, preference="muscle_gain")
        sols = self.actuary.plan(cons, self.details)
        self.assertGreater(len(sols), 0, "增肌场景应有可行解")
        for s in sols:
            self.assertGreaterEqual(s.nutrition.protein, 40)
            self.assertLessEqual(s.price, 50)

    def test_budget_persona(self):
        """省钱党：20 元内吃饱（无营养硬约束）。"""
        cons = Constraints(budget=20, preference="budget")
        sols = self.actuary.plan(cons, self.details)
        self.assertGreater(len(sols), 0, "省钱场景应有可行解")
        for s in sols:
            self.assertLessEqual(s.price, 20)
        # 最贵方案不高于任何未入选可行解的同类（Top3 按分数序）
        scores = [s.score for s in sols]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_blacklist_respected(self):
        """黑名单：不吃牛肉 → 候选不得含'牛'堡。"""
        cons = Constraints(budget=45, min_protein=20, blacklist=["牛"])
        sols = self.actuary.plan(cons, self.details)
        for s in sols:
            for item in s.items:
                self.assertNotIn("牛", item, f"黑名单失效：{item}")

    def test_top3_diversity(self):
        """Top3 主食互不相同。"""
        cons = Constraints(budget=50, preference="balanced")
        sols = self.actuary.plan(cons, self.details)
        mains = [s.main_names() for s in sols]
        self.assertEqual(len(mains), len(set(mains)), "Top3 主食应互不相同")

    def test_meal_variant_swap_priced(self):
        """套餐变体差价正确：小杯玉米杯 -0.5 元。"""
        cons = Constraints(budget=50, max_kcal=800, min_protein=20,
                           preference="weight_loss")
        sols = self.actuary.plan(cons, self.details)
        meal_sols = [s for s in sols if s.kind == "meal" and "玉米杯" in " ".join(s.items)]
        for s in meal_sols:
            self.assertAlmostEqual(s.price, 36.5 - 0.5, delta=0.01)  # 36.0 元


if __name__ == "__main__":
    unittest.main()
