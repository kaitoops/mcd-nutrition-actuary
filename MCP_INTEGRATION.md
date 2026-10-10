# MCP 接入说明（MCP Integration）

本文说明麦麦营养精算师如何接入并使用麦当劳中国 MCP 服务。

## 1. 使用的 MCP Server

| 项 | 值 |
|---|---|
| Server | 麦当劳中国官方 MCP（`mcd-mcp`） |
| 接入地址 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP |
| 鉴权 | `Authorization: Bearer <MCP_TOKEN>`（Token 在 [open.mcd.cn/mcp](https://open.mcd.cn/mcp) 控制台申请） |
| 限流 | 600 次/分钟/Token（本 Skill 一次完整精算 ≤8 次调用，远低于限额） |

## 2. 使用的 Tool 清单

| Tool | 用途 | 本项目中的角色 | 调用时机 |
|---|---|---|---|
| `list-nutrition-foods` | 餐品营养信息（能量/蛋白/脂肪/碳水/钠/钙） | **核心数据源**：160 餐品官方营养表，精算的"原材料价格表" | 每次精算 1 次（快照可复用） |
| `query-meals` | 当前门店可售菜单（code/分类/价格） | **核心数据源**：候选餐品与价格 | 每次精算 1 次 |
| `query-meal-detail` | 套餐组成与可替换项（rounds/choices/diffPrice） | **差异化杠杆**：套餐内替换展开（如中薯条→玉米杯 -0.5 元 -236kcal） | 每次精算 ≤3-5 个套餐 |
| `query-nearby-stores` | 附近门店（storeCode/距离/营业时间） | 入口：定位用户门店 | 每次精算 1 次（beType=1 到店自提） |
| `calculate-price` | 含优惠价格试算（单位：分） | **实付复核**：Top1 方案价格校准 | 每次精算 ≤2 次 |
| `query-store-coupons` | 门店可用优惠券 | 叠加优惠：有券报券，无券提示一键领券（`auto-bind-coupons`） | 每次精算 1 次 |
| `now-time-info` | 服务器时间 | 时段感知（早餐/正餐菜单切换） | 每次精算 1 次 |

## 3. 调用流程

```
Step 0  now-time-info                 → 时段感知
Step 1  （对话）收集约束               → 预算/热量/蛋白/忌口/偏好
Step 2  query-nearby-stores           → 定门店（storeCode）
Step 3  query-meals ┐（并行）          → 菜单+价格
        list-nutrition-foods ┘       → 官方营养表
Step 4  （本地）转存 JSON             → menu.json / cons.json / details.json
Step 5  （本地）scripts/actuary_cli.py → 组合枚举+约束过滤+多目标评分 → Top3
Step 6  calculate-price              → Top1 实付复核（分→元）
        query-store-coupons          → 券叠加提示
Step 7  输出精算报告（markdown）
```

**关键工程决策**：Step 3-5 之间，MCP 数据以 JSON 文件中转给本地精算引擎（`src/optimizer.py`），而非让 LLM 在对话中枚举组合。理由：约 1 万候选的枚举与评分是确定性计算，代码执行零误差、零 token 边际成本；LLM 只做数据搬运与报告解读。这也是本项目的省算力设计核心。

## 4. 名称匹配机制（弥补数据缺口）

官方营养表 `list-nutrition-foods` **不含 productCode**，本项目用三级名称匹配关联（`src/matcher.py`）：

1. 别名表直查（如菜单"麦咖啡™美式"→营养表"冰美式中杯"）
2. 标准化后精确匹配（去 ™®、统一全/半角括号、去装饰符号）
3. 双向子串包含，取长度差最小者（如菜单"薯条"→营养表"中薯条"）

匹配失败的餐品不计入候选，报告如实标注"营养匹配度"。

## 5. 业务价值

1. **把官方营养数据变成决策力**：`list-nutrition-foods` 提供了完整营养表，但官方渠道没有"给定预算+营养目标反推最优组合"的能力——本项目补上这一环。
2. **套餐内替换是被低估的杠杆**：`query-meal-detail` 的 diffPrice 揭示了同价/微差价的热量优化空间（如 -0.5 元换 -236kcal），用户无需放弃爱吃的汉堡。
3. **面向真实决策链路**：门店→菜单→组合→算价→券，全部走官方 MCP，输出可直接用于点餐决策；下单仍由用户确认，符合"建议类"定位。
4. **确定性精算 + LLM 编排**的混合架构，为"轻量、低成本、可复现"的 MCP Skill 提供参考实现。
