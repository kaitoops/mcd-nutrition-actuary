"""数据模型：麦麦营养精算师（纯标准库，零第三方依赖）。"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Nutrition:
    """营养量（kcal / g / mg）。"""
    kcal: float = 0.0
    protein: float = 0.0
    fat: float = 0.0
    carb: float = 0.0
    sodium: float = 0.0
    calcium: float = 0.0

    def add(self, other: "Nutrition") -> "Nutrition":
        self.kcal += other.kcal
        self.protein += other.protein
        self.fat += other.fat
        self.carb += other.carb
        self.sodium += other.sodium
        self.calcium += other.calcium
        return self

    def scale(self, k: float) -> "Nutrition":
        self.kcal *= k
        self.protein *= k
        self.fat *= k
        self.carb *= k
        self.sodium *= k
        self.calcium *= k
        return self

    def is_zero(self) -> bool:
        return all(v == 0 for v in (self.kcal, self.protein, self.fat, self.carb,
                                    self.sodium, self.calcium))


@dataclass
class MenuItem:
    """菜单单品（来自 query-meals）。price 单位：元。"""
    code: str
    name: str
    price: float
    category: str = ""
    tags: List[str] = field(default_factory=list)
    role: str = ""  # main / side / drink / None


@dataclass
class Choice:
    """套餐内一个可选子项（来自 query-meal-detail rounds[].choices[]）。"""
    code: str
    name: str
    diff_price: float = 0.0   # 元，相对默认选择的差价
    is_default: bool = False


@dataclass
class ComboRound:
    """套餐的一个选配轮次。"""
    name: str
    choices: List[Choice] = field(default_factory=list)


@dataclass
class MealDetail:
    """套餐详情（来自 query-meal-detail）。"""
    code: str
    name: str
    base_price: float = 0.0   # 元（菜单 currentPrice）
    rounds: List[ComboRound] = field(default_factory=list)


@dataclass
class Constraints:
    """用户约束。None 表示不限制。"""
    budget: float = 50.0            # 预算上限（元）
    max_kcal: Optional[float] = None     # 热量上限
    min_protein: Optional[float] = None  # 蛋白质下限
    max_sodium: Optional[float] = None   # 钠上限（mg）
    blacklist: List[str] = field(default_factory=list)  # 不吃的关键词
    preference: str = "balanced"    # balanced / weight_loss / muscle_gain / budget


@dataclass
class Solution:
    """一个完整推荐方案。"""
    kind: str = "combo"             # combo(单品组合) / meal(套餐变体)
    items: List[str] = field(default_factory=list)       # 展示名
    codes: List[str] = field(default_factory=list)       # MCP productCode（下单可用）
    main_item: str = ""             # 主食名（多样性去重键）
    price: float = 0.0
    nutrition: Nutrition = field(default_factory=Nutrition)
    matched_ratio: float = 1.0      # 营养匹配覆盖率
    score: float = 0.0
    base_name: str = ""             # 套餐名（kind=meal 时）
    swaps: str = ""                 # 套餐变体相对默认的调整说明

    def main_names(self) -> frozenset:
        return frozenset({self.main_item} if self.main_item else set(self.items))
