"""麦麦营养精算师 · 核心算法包。"""
from .matcher import NutritionMatcher, normalize
from .models import Choice, ComboRound, Constraints, MealDetail, MenuItem, Nutrition, Solution
from .optimizer import NutritionActuary, build_meal_details, categorize, format_report, parse_diff_price

__all__ = [
    "NutritionMatcher", "normalize",
    "Choice", "ComboRound", "Constraints", "MealDetail", "MenuItem", "Nutrition", "Solution",
    "NutritionActuary", "build_meal_details", "categorize", "format_report", "parse_diff_price",
]
