"""麦麦营养精算师 · 多约束组合优化器。

设计原则（贴合本项目约束）：
- 零第三方依赖，纯 Python 标准库；
- 候选空间规模（约 1 万组合）允许精确枚举 + 打分，不需要启发式近似；
- 单品组合与套餐变体统一为 Solution 评分，输出 Top3 且主食互不相同（多样性）。

数据来源：
- menu:        query-meals 解析后的 MenuItem 列表
- meal_details: query-meal-detail 解析后的 MealDetail 列表（可选）
- nutrition:    matcher（营养表按名称匹配）
"""
import re
from typing import Dict, List, Optional

from .matcher import NutritionMatcher, normalize
from .models import Choice, ComboRound, Constraints, MealDetail, MenuItem, Nutrition, Solution

# 角色分类关键词（基于实测菜单名；先 drink 后 side 后 main，避免误判）
_DRINK_RE = re.compile(r"可乐|雪碧|红茶|咖啡|牛奶|豆浆|果汁|怡泉|美汁源|奶铁|燕麦|黑巧|抹茶|朱古力|麦旋酷|雪冰|阿芙佳朵")
_SIDE_RE = re.compile(r"薯条|玉米杯|苹果片|沙拉|派|新地|旋风|拉明顿|香油条|薯饼|趣鸡球|翅|鸡柳|脆汁鸡|麦乐鸡")
_MAIN_RE = re.compile(r"堡|卷|鳕鱼|麦香鱼|麦香鸡|板烧|无霸|麦满分|营养卷|粥|鸡排")

_DIFF_PRICE_RE = re.compile(r"([+-])\s*¥\s*([0-9.]+)")

# 趣味换算：60kg 成人慢跑约 60 kcal/km（机制级近似，报告展示用）
RUN_KCAL_PER_KM = 60.0


def categorize(name: str) -> Optional[str]:
    """菜单名 → main/side/drink；无法分类返回 None（不参与组合）。"""
    n = normalize(name)
    if _DRINK_RE.search(n):
        return "drink"
    if _SIDE_RE.search(n):
        return "side"
    if _MAIN_RE.search(n):
        return "main"
    return None


def parse_diff_price(s: str) -> float:
    """解析套餐 diffPrice 字符串："+ ¥1" → 1.0，"- ¥0.5" → -0.5，空/异常 → 0。"""
    if not s:
        return 0.0
    m = _DIFF_PRICE_RE.search(s)
    if not m:
        return 0.0
    sign = 1 if m.group(1) == "+" else -1
    return sign * float(m.group(2))


def build_meal_details(raw_details: List[dict], menu_prices: Dict[str, float]) -> List[MealDetail]:
    """把 query-meal-detail 原始返回解析成 MealDetail。

    raw_details[i] 形如 {"code","name","rounds":[{"name","choices":[{"code","name","isDefault","diffPrice"}]}]}
    menu_prices: code -> 菜单现价（元）
    """
    out = []
    for d in raw_details:
        rounds = []
        for r in d.get("rounds", []):
            choices = []
            for c in r.get("choices", []):
                choices.append(Choice(
                    code=str(c.get("code", "")),
                    name=c.get("name", ""),
                    diff_price=parse_diff_price(c.get("diffPrice", "")),
                    is_default=(c.get("isDefault") == 1),
                ))
            rounds.append(ComboRound(name=r.get("name", ""), choices=choices))
        md = MealDetail(
            code=str(d.get("code", "")),
            name=d.get("name", ""),
            base_price=menu_prices.get(str(d.get("code", "")), 0.0),
            rounds=rounds,
        )
        out.append(md)
    return out


class NutritionActuary:
    """核心精算引擎：约束过滤 + 多目标评分 + Top3 多样化输出。"""

    def __init__(self, menu: List[MenuItem], matcher: Optional[NutritionMatcher] = None):
        self.matcher = matcher or NutritionMatcher()
        self.menu = menu
        self.mains = [m for m in menu if m.role == "main"]
        self.sides = [m for m in menu if m.role == "side"]
        self.drinks = [m for m in menu if m.role == "drink"]

    # ---------- 候选生成 ----------

    def _item_nutrition(self, item: MenuItem):
        """单品营养 + 是否匹配成功。"""
        nutri = self.matcher.match(item.name)
        return nutri, nutri is not None

    def _combo_candidates(self, cons: Constraints):
        """单品组合候选：1 主食 + 0~1 小食 + 0~1 饮品。"""
        for m in self.mains:
            mn, m_ok = self._item_nutrition(m)
            if not m_ok:
                continue
            for s in list(self.sides) + [None]:
                sn, s_ok = (True, Nutrition()) if s is None else self._item_nutrition(s)
                if s is not None and not s_ok:
                    continue
                for d in list(self.drinks) + [None]:
                    dn, d_ok = (True, Nutrition()) if d is None else self._item_nutrition(d)
                    if d is not None and not d_ok:
                        continue
                    items = [m.name] + ([s.name] if s else []) + ([d.name] if d else [])
                    codes = [m.code] + ([s.code] if s else []) + ([d.code] if d else [])
                    price = m.price + (s.price if s else 0) + (d.price if d else 0)
                    nutri = Nutrition(); nutri.add(mn)
                    if s: nutri.add(sn)
                    if d: nutri.add(dn)
                    yield Solution(kind="combo", items=items, codes=codes,
                                   main_item=m.name,
                                   price=round(price, 2), nutrition=nutri)

    def _meal_candidates(self, details: List[MealDetail]):
        """套餐变体候选：对每轮 choices 做笛卡尔积展开。"""
        for md in details:
            if not md.rounds or md.base_price <= 0:
                continue
            price = md.base_price
            # 逐轮展开，维护 (items, codes, diff_sum, nutrition) 的候选池
            pool = [([], [], 0.0, Nutrition())]
            ok = True
            for rnd in md.rounds:
                nxt = []
                for ch in rnd.choices:
                    nutri = self.matcher.match(ch.name)
                    if nutri is None:
                        continue  # 该子项营养未知 → 不展开该选择
                    for items, codes, diff, base_nutri in pool:
                        nxt.append((items + [ch.name], codes + [ch.code],
                                    diff + ch.diff_price,
                                    Nutrition(**vars(base_nutri)).add(nutri)))
                if not nxt:
                    ok = False
                    break
                pool = nxt
            if not ok:
                continue
            for items, codes, diff, nutri in pool:
                swaps = self._describe_swaps(md, items)
                yield Solution(kind="meal", items=items, codes=codes,
                               price=round(price + diff, 2), nutrition=nutri,
                               base_name=md.name, swaps=swaps)

    def _describe_swaps(self, md: MealDetail, items: List[str]) -> str:
        """生成"相对默认配置"的调整说明（只列非默认项）。"""
        swaps = []
        for rnd in md.rounds:
            default = next((c.name for c in rnd.choices if c.is_default), None)
            picked = next((i for i in items if any(c.name == i for c in rnd.choices)), None)
            if default and picked and picked != default:
                swaps.append(f"{default}→{picked}")
        return "，".join(swaps) if swaps else "官方默认配置"

    # ---------- 过滤与评分 ----------

    def _violates(self, sol: Solution, cons: Constraints) -> bool:
        if cons.budget is not None and sol.price > cons.budget:
            return True
        n = sol.nutrition
        if cons.max_kcal is not None and n.kcal > cons.max_kcal:
            return True
        if cons.min_protein is not None and n.protein < cons.min_protein:
            return True
        if cons.max_sodium is not None and n.sodium > cons.max_sodium:
            return True
        bl = [normalize(w) for w in cons.blacklist if w]
        for item in sol.items:
            ni = normalize(item)
            if any(w in ni for w in bl):
                return True
        return False

    # 各偏好的权重（protein 密度/总量、低热量、价格、均衡）
    _WEIGHTS = {
        "balanced":    {"eff": 0.30, "kcal": 0.10, "protein": 0.30, "price": 0.30},
        "weight_loss": {"eff": 0.40, "kcal": 0.30, "protein": 0.20, "price": 0.10},
        "muscle_gain": {"eff": 0.20, "kcal": 0.00, "protein": 0.55, "price": 0.25},
        "budget":      {"eff": 0.15, "kcal": 0.00, "protein": 0.25, "price": 0.60},
    }

    def _score(self, sol: Solution, cons: Constraints) -> float:
        w = self._WEIGHTS.get(cons.preference, self._WEIGHTS["balanced"])
        n = sol.nutrition
        kcal = max(n.kcal, 1.0)

        eff = min(n.protein / kcal * 1000 / 60.0, 1.2)          # 蛋白密度(g/1000kcal) / 60 归一
        kcal_score = max(0.0, 1.0 - n.kcal / (cons.max_kcal or 900))  # 越接近上限扣越多
        protein_target = max(cons.min_protein or 20.0, 20.0)
        protein_score = min(n.protein / protein_target, 1.25)
        price_score = max(0.0, 1.0 - (sol.price / (cons.budget or 50)) ** 2)

        score = (w["eff"] * eff + w["kcal"] * kcal_score
                 + w["protein"] * protein_score + w["price"] * price_score)

        # 惩罚项：钠超标、脂肪供能比过高、营养匹配不全
        if n.sodium > 1500:
            score -= min(0.25, (n.sodium - 1500) / 100 * 0.02)
        fat_ratio = n.fat * 9 / kcal
        if fat_ratio > 0.40:
            score -= min(0.20, (fat_ratio - 0.40) * 1.5)
        score *= sol.matched_ratio
        return round(score, 4)

    # ---------- 主入口 ----------

    def plan(self, cons: Constraints, meal_details: Optional[List[MealDetail]] = None,
             top_k: int = 3) -> List[Solution]:
        candidates = list(self._combo_candidates(cons))
        if meal_details:
            candidates.extend(self._meal_candidates(meal_details))

        feasible = []
        for sol in candidates:
            if self._violates(sol, cons):
                continue
            sol.score = self._score(sol, cons)
            feasible.append(sol)

        feasible.sort(key=lambda s: s.score, reverse=True)

        # 主食多样性：不同主食组合才入 Top K（避免 3 个方案只差饮料）
        seen, result = set(), []
        for sol in feasible:
            key = sol.main_names()
            if key in seen:
                continue
            seen.add(key)
            result.append(sol)
            if len(result) >= top_k:
                break
        return result


# ---------- 报告生成 ----------

def format_report(solutions: List[Solution], cons: Constraints,
                  matcher: Optional[NutritionMatcher] = None) -> str:
    """生成 markdown 精算报告（Skill 层直接复用）。"""
    lines = []
    cons_desc = [f"预算 ≤{cons.budget} 元"]
    if cons.max_kcal: cons_desc.append(f"热量 ≤{int(cons.max_kcal)} kcal")
    if cons.min_protein: cons_desc.append(f"蛋白 ≥{int(cons.min_protein)} g")
    if cons.max_sodium: cons_desc.append(f"钠 ≤{int(cons.max_sodium)} mg")
    pref_map = {"balanced": "均衡", "weight_loss": "减脂", "muscle_gain": "增肌", "budget": "省钱"}
    lines.append(f"## 🧮 麦麦营养精算报告")
    lines.append(f"约束：{' · '.join(cons_desc)} · 偏好：{pref_map.get(cons.preference, cons.preference)}")
    lines.append("")

    for i, s in enumerate(solutions, 1):
        n = s.nutrition
        tag = f"（{s.base_name}｜{s.swaps}）" if s.kind == "meal" else ""
        lines.append(f"### 方案 {i}：{(' + '.join(s.items))}{tag}")
        lines.append(f"- 实付：**{s.price:.1f} 元**（预算 {cons.budget} 元内{'，还剩 ' + format(cons.budget - s.price, '.1f') + ' 元' if s.price <= cons.budget else ''}）")
        lines.append(f"- 热量：**{n.kcal:.0f} kcal**｜蛋白：{n.protein:.0f} g｜脂肪：{n.fat:.0f} g｜碳水：{n.carb:.0f} g｜钠：{n.sodium:.0f} mg｜钙：{n.calcium:.0f} mg")
        lines.append(f"- 消耗这顿 ≈ 慢跑 **{n.kcal / RUN_KCAL_PER_KM:.1f} km**（60kg 成人）")
        lines.append(f"- 营养匹配度：{s.matched_ratio * 100:.0f}%（营养数据来自麦当劳 MCP list-nutrition-foods）")
        lines.append(f"- 精算得分：{s.score:.3f}")
        lines.append("")
    lines.append("> 数据来源：麦当劳中国 MCP（菜单/营养/价格实时接口）。"
                 "营养按餐品名称匹配官方营养表计算；特调（去酱/去冰等）按官方默认处理。")
    return "\n".join(lines)
