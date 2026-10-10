# 🧮 麦麦营养精算师（McNutrition Actuary）

> 输入预算和营养目标，AI 精算麦当劳菜单的全部组合，告诉你怎么吃最划算、最达标。
> **同价微调配餐，砍掉几百大卡**：不改店、不改主食，把中薯条换成小杯玉米杯（-236 kcal 还便宜 5 毛）、可乐换成无糖可乐（-147 kcal 不加钱）。

基于 [麦当劳中国官方 MCP 服务](https://github.com/M-China/mcd-mcp-server)开发的参赛 Skill —— 2026 麦当劳程序员创意开发大赛（M-CODE）作品。

**English**: McNutrition Actuary is an AI skill built on McDonald's China official MCP server. Give it a budget, a calorie cap and a protein floor, and it exhaustively enumerates ~10,000 menu combinations to return the Top 3 meal plans — each with live-priced checkout totals (via `calculate-price`), full nutrition facts, and exercise equivalents. It also finds same-price menu swaps that cut hundreds of kcal (medium fries → corn cup: −236 kcal and ¥0.5 cheaper). Zero third-party dependencies, deterministic local optimizer, ≤8 MCP calls per consultation. Entry for the 2026 McDonald's China Developer Innovation Challenge.

## ✨ 它能做什么

| 模式 | 你说 | 它做 |
|---|---|---|
| 🏃 减脂精算 | "40 块以内，600 大卡以内，蛋白质要够" | 全菜单组合枚举 → Top3 方案（热量/蛋白/钠/钙全表） |
| 💪 增肌精算 | "50 块以内，蛋白 40g 以上" | 蛋白密度优先排序，饱腹感换算 |
| 💰 省钱精算 | "20 块在麦当劳吃饱" | 预算硬约束下营养分最高的组合（含随心配 1+1） |
| 🍔 套餐微调 | "巨无霸套餐怎么点最低卡" | 套餐内 round 级替换展开：差价与热量节省一目了然 |

每个方案附带：**实付价**（`calculate-price` 实时复核）· **吃完要跑几公里** · **营养匹配度**（对官方营养表 160 餐品名称匹配）。

## 🚀 快速开始

### 方式 A：WorkBuddy Skill（推荐）

1. 前置：到 [open.mcd.cn/mcp](https://open.mcd.cn/mcp) 申请 MCP Token（手机号登录 → 控制台 → 激活）
2. WorkBuddy 左侧【连接器】→【自定义连接器】→【配置 MCP】：

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": {
        "Authorization": "Bearer YOUR_MCP_TOKEN"
      }
    }
  }
}
```

3. 启用后，把 `skill/SKILL.md` 安装为 WorkBuddy Skill，然后直接说：
   > "帮我在 40 块以内配一顿 600 大卡以内的麦当劳，蛋白质要 25 克以上，深圳科技园"

### 方式 B：纯 CLI（无需 LLM）

```bash
# 1. 准备 cons.json（约束）与 menu.json（MCP 取数结果）
# 2. 跑精算
python scripts/actuary_cli.py --constraints cons.json --menu menu.json --out report.md
```

或直接体验离线演示（内置深圳同方信息港店实测数据）：

```bash
python examples/run_demo.py
```

## 🧠 工作原理

```
用户约束(预算/热量/蛋白/忌口/偏好)
        │
        ▼
┌─ 麦当劳 MCP ──────────────┐     ┌─ 本地精算引擎（确定性代码）─┐
│ query-nearby-stores 门店   │     │ matcher.py  名称三级匹配     │
│ query-meals          菜单  │ ──▶ │ optimizer.py 组合枚举+评分   │
│ query-meal-detail    套餐  │     │   · 约束过滤(硬)             │
│ calculate-price      算价  │     │   · 多目标评分(软)           │
│ list-nutrition-foods 营养  │     │   · Top3 主食互异            │
└───────────────────────────┘     └──────────────────────────────┘
                                          │
                                          ▼
                              Top3 精算报告（价格/营养/跑几公里）
```

**为什么精算不用 LLM 心算？** 组合枚举（约 1 万候选）与差价解析是确定性计算，LLM 心算易错且贵；代码一次写好，永久零边际成本——全程一次精算仅消耗 ≤8 次 MCP 调用与极少 token。

## 🎯 目标用户

- **健身/减脂党**：热量与蛋白有硬指标，但又想吃顿麦当劳解馋
- **学生党/预算敏感**：钱要花在刀刃上，顺带别吃太垃圾
- **带娃家长**：开心乐园餐之外想快速配个达标的成人餐
- **Agent 开发者**：一个"MCP 取数 + 本地确定性精算"的参考实现

## 🔍 与同类参赛项目的差异

| | 省钱凑单类（如麦门精算师） | 本项目 |
|---|---|---|
| 优化目标 | 价格最低 | **营养×预算多目标**（蛋白/热量/钠/钙/性价比） |
| 数据深挖 | 优惠券 | **官方营养表 160 餐品** + 套餐 round 级替换差价 |
| 输出 | 省钱报告 | 营养精算报告 + 运动换算 + 匹配度标注 |

## 📁 项目结构

```
mcd-nutrition-actuary/
├── skill/SKILL.md            # WorkBuddy Skill 编排文档（MCP 调用流程）
├── src/
│   ├── matcher.py            # 营养表名称三级匹配（别名/标准化/子串）
│   ├── optimizer.py          # 多约束组合优化器 + 报告生成
│   ├── models.py             # 数据模型
│   └── data/nutrition_snapshot.py  # 官方营养表快照（160 餐品）
├── scripts/actuary_cli.py    # CLI 入口：JSON 进 → 报告出
├── tests/test_optimizer.py   # 15 个用例（diffPrice 解析/匹配/分类/四类人设）
├── examples/run_demo.py      # 端到端演示（减脂党场景）
├── docs/api-notes.md         # MCP 数据契约实测笔记
├── MCP_INTEGRATION.md        # MCP 接入说明（参赛必交）
└── CONTEST_DECLARATION.md    # 参赛声明（官方原样）
```

## ✅ 测试

```bash
python -m unittest discover -s tests   # 15/15 通过，零第三方依赖
```

## 📄 数据来源与免责

- 菜单/价格/营养/门店数据均来自麦当劳中国官方 MCP 服务实时接口，营养表快照日期 2026-10-10。
- 本项目为个人参赛作品，非麦当劳官方产品；输出仅供参考，不构成营养或医疗建议；特殊人群请咨询专业人士；餐品价格与供应以门店实时为准。
- 免责与声明详见 [CONTEST_DECLARATION.md](CONTEST_DECLARATION.md)。

## 📄 License

[MIT](LICENSE)
