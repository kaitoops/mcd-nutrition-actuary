"""名称匹配器：弥合「营养表无 productCode」缺口。

麦当劳 MCP 的 list-nutrition-foods 只返回 productName，不含餐品编码，
因此营养数据与菜单/套餐子项的关联完全依赖名称匹配。

三级降级策略（标准实现优先，避免自研复杂模糊算法）：
  1. MENU_ALIAS 别名表直查（官方菜单名 → 营养表名）
  2. 标准化后精确相等
  3. 标准化后子串包含（双向），取长度差最小者
"""
import re
from typing import Optional

from .data.nutrition_snapshot import NUTRITION_ROWS, MENU_ALIAS
from .models import Nutrition

# 真实零营养饮品（营养全 0 不是缺数据，是真的 0）
_ZERO_WHITELIST = ("无糖可口可乐", "锡兰红茶", "川宁伯爵红茶", "纯悦")

_DECOR_RE = re.compile(r"[【】\[\]“”\"'‘’]")
_BRACKET_RE = re.compile(r"[（(][^（）()]*[)）]")


def normalize(name: str) -> str:
    """名称标准化：去 ™®、去括号内容、去装饰符号与空白。"""
    s = name.strip()
    s = s.replace("™", "").replace("®", "")
    s = _BRACKET_RE.sub("", s)
    s = _DECOR_RE.sub("", s)
    s = re.sub(r"\s+", "", s)
    return s


class NutritionMatcher:
    """营养表索引 + 名称三级匹配。"""

    def __init__(self, rows=None):
        rows = rows if rows is not None else NUTRITION_ROWS
        self._by_norm = {}   # normalized_name -> Nutrition
        self._display = {}   # normalized_name -> 原始名（报告展示用）
        for row in rows:
            name, kj, kcal, p, f, c, na, ca = row
            # 占位品（营养未知全 0 且不在零营养白名单）不进索引
            if (kcal == 0 and p == 0 and f == 0 and c == 0
                    and not any(w in name for w in _ZERO_WHITELIST)):
                continue
            n = normalize(name)
            if n and n not in self._by_norm:
                self._by_norm[n] = Nutrition(kcal, p, f, c, na, ca)
                self._display[n] = name

    def match(self, menu_name: str) -> Optional[Nutrition]:
        """菜单名 → 营养数据；匹配不到返回 None（调用方按 unmatched 处理）。"""
        if not menu_name:
            return None
        # 1) 别名表
        if menu_name in MENU_ALIAS:
            return self._by_norm.get(normalize(MENU_ALIAS[menu_name]))
        n = normalize(menu_name)
        # 2) 精确
        if n in self._by_norm:
            return self._by_norm[n]
        # 3) 子串双向包含（长度差最小 = 最具体的匹配）
        cands = [k for k in self._by_norm
                 if len(k) >= 2 and (k in n or n in k)]
        if cands:
            best = min(cands, key=lambda k: (abs(len(k) - len(n)), k))
            return self._by_norm[best]
        return None

    def display_name(self, menu_name: str) -> str:
        """匹配到的营养表原始名（用于报告标注）。"""
        nutri = self.match(menu_name)
        if nutri is None:
            return menu_name
        n = normalize(MENU_ALIAS.get(menu_name, menu_name))
        if n in self._display:
            return self._display[n]
        cands = [k for k in self._display
                 if len(k) >= 2 and (k in n or n in k)]
        if cands:
            best = min(cands, key=lambda k: (abs(len(k) - len(n)), k))
            return self._display[best]
        return menu_name
