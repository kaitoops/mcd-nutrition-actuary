---
name: mcnutrition-actuary
description: 麦麦营养精算师——基于麦当劳中国 MCP 的营养×预算双约束套餐精算助手。当用户想"按预算/热量/蛋白目标吃麦当劳"、"搭配一顿不超标的麦当劳"、"今天麦麦吃什么划算又健康"时使用。给出 Top3 套餐组合 + 完整营养表 + 实付价 + 趣味运动换算，只建议不下单。
---

# 麦麦营养精算师（McNutrition Actuary）

> 输入预算和营养目标，AI 精算麦当劳菜单的全部组合，告诉你怎么吃最划算、最达标。
> 核心理念：**不改店不改主食，同价微调配餐就能砍掉几百大卡**。

## 前置条件

- 已在 WorkBuddy 配置并启用 `mcd-mcp` 连接器（Streamable HTTP，`https://mcp.mcd.cn`）
- MCP Token 有效（限流 600 次/分钟）

## ⚠️ 总原则（必须遵守）

1. **请求预算**：一次完整精算 ≤ 8 次 MCP 调用（门店1 + 菜单1 + 营养1 + 套餐详情≤3 + 算价≤2）。超了说明流程有问题，停下来检查。
2. **精算交给代码，不做心算枚举**：组合枚举与评分必须用 `scripts/actuary_cli.py`（确定性算法），AI 只负责取数、转存 JSON、解读报告。禁止在对话中手动枚举几十个组合。
3. **只建议不下单**：本 Skill 输出到"方案报告"为止。用户明确要求下单时，提示核对后引导走 `create-order`（下单前必须复述订单明细并获用户确认）。
4. **特调按官方默认处理**：modification（去酱/去冰等）对热量影响小且传参复杂，报告里注明"特调按默认"，用户主动问再展开。

## 工作流程（7 步）

### Step 0 感知时间
调 `now-time-info`。10:30 前是早餐菜单、10:30 后是正餐——影响后续菜单预期。

### Step 1 收集约束（一次性问齐，不挤牙膏）

必问：**预算**（元）。可选（不答就不限）：热量上限 kcal、蛋白下限 g、忌口黑名单、偏好（减脂 weight_loss / 增肌 muscle_gain / 省钱 budget / 均衡 balanced）。

用户新手没有任何想法时，直接推荐默认三档：减脂档（≤600kcal·≥25g 蛋白）、增肌档（≥40g 蛋白）、省钱档（≤25 元）。

### Step 2 定门店
用户给了城市+地标 → `query-nearby-stores(searchType=2, city, keyword, beType=1)`。
未给位置 → 问"你在哪个城市、大概哪片？"（到店自提 beType=1 链路最简，全流程无需 beCode）。
展示前 3 家（名称/距离/地址），让用户选一家，记 `storeCode`。

### Step 3 拉菜单 + 营养表（可并行）
- `query-meals(storeCode, orderType=1, beType=1)` → 菜单分类 + 餐品 code/价格
- `list-nutrition-foods()` → 官方营养表（160 餐品：kcal/蛋白/脂肪/碳水/钠/钙）

### Step 4 转存 JSON（写入临时文件，例如 workspace 下 `_mcd_actuary/`）

- `menu.json`：把菜单展平为 `[{"code","name","price","category"}]`
- `details.json`（可选）：挑 3~5 个"用户可能感兴趣或官方主推"的套餐 code，调 `query-meal-detail` 存原始 data 数组。**优先选含"套餐"tag 且用户预算范围内的**。
- `cons.json`：`{"budget":40,"max_kcal":600,"min_protein":25,"max_sodium":null,"blacklist":[],"preference":"weight_loss"}`

### Step 5 跑精算引擎

```bash
python scripts/actuary_cli.py --constraints cons.json --menu menu.json --meal-details details.json --out report.md
```

脚本自动完成：名称匹配营养表 → 单品组合+套餐变体全枚举 → 约束过滤 → 多目标评分 → Top3（主食互不相同）。退出码 2 = 无可行解，此时按 `--top-k` 提示放宽最紧的约束（通常是预算或蛋白下限）。

### Step 6 实付价复核（可选但推荐）
对 Top1 调 `calculate-price(storeCode, orderType=1, beType=1, items=[{productCode,quantity}...])` 复核实付（返回单位是**分**，÷100）。若与报告价差超 1 元，以 calculate-price 为准并在报告标注"以门店实时计价为准"。顺带调 `query-store-coupons`：**有券 → 把券码报给用户并说明用法；无券 → 提示"可以让我帮你一键领券（auto-bind-coupons）后再精算一轮"**。

### Step 7 输出报告
直接呈现 `report.md` 内容，末尾固定追问一句：
"想按某个方案下单可以告诉我；也可以换个玩法：调低预算 / 加忌口 / 换成增肌档再精算一轮。"

## 数据契约速查（AI 取数时对照）

| 事项 | 结论 |
|---|---|
| 营养表 | `list-nutrition-foods` 无参调用，纯文本表，字段 `{productName,energyKj,energyKcal,protein,fat,carbohydrate,sodium,calcium}`，**无 productCode**，靠名称匹配（内置快照已含 alias 与标准化） |
| 菜单价格单位 | query-meals 的 `currentPrice` 是**元**（字符串） |
| 算价单位 | calculate-price 全部是**分**，展示 ÷100 |
| 套餐差价 | detail 的 `diffPrice` 形如 `"+ ¥1"` / `"- ¥0.5"`，脚本已解析 |
| 限流 | 600 次/分钟，429 时等 60 秒重试 |
| 401 | Token 失效，引导去 open.mcd.cn/mcp 重新激活 |

## 边界与安全

- 本 Skill 是**建议类**工具，不构成营养/医疗建议；营养数据来自麦当劳官方 MCP，按名称匹配可能有极少数误差，报告已标注匹配度。
- 未成年人、孕期等特殊人群请咨询专业营养师（报告固定提示语已覆盖）。
- 绝不把 MCP Token 写入任何输出、报告或文件；绝不代替用户确认订单。
