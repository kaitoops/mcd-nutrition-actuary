# MCP 数据契约笔记（2026-10-10 实测）

> 本文记录麦麦营养精算师开发期间对麦当劳中国 MCP Server（`https://mcp.mcd.cn`）6 个核心工具的实测返回结构。所有结论均为真实调用结果，是 `src/` 优化器设计的数据契约。

## 0. 通用约定

- 传输：Streamable HTTP，`Authorization: Bearer <MCP_TOKEN>`
- 限流：**600 次/分钟/Token**，超限 429
- 价格单位：**分**（calculate-price 返回值需 ÷100 转元）；菜单 query-meals 的 currentPrice 单位是**元**（字符串）——两处不一致，注意换算
- 通用响应包裹：`{"success":bool, "code":int, "message":str, "traceId":str, "data":...}`

## 1. list-nutrition-foods（营养表 · 核心数据源）

入参：无

返回：**纯文本表格**（非 JSON），格式 `[160]{productName,nutritionDescription,energyKj,energyKcal,protein,fat,carbohydrate,sodium,calcium}`，每行一个餐品。

| 字段 | 含义 | 单位 |
|---|---|---|
| productName | 餐品名 | — |
| energyKj / energyKcal | 能量 | kJ / kcal |
| protein / fat / carbohydrate | 三大宏量 | g |
| sodium / calcium | 钠 / 钙 | mg |

样例行：
```
巨无霸,null,2146,513,27,26,42,961,171      # 513 kcal, 27g 蛋白
无糖可口可乐中杯,null,0,0,0,0,1,35,0       # 0 kcal
中薯条,null,1210,289,4,12,38,165,18
小杯玉米杯,null,223,53,2,1,7,1,6
```

⚠️ **关键缺口：营养表无 productCode**。营养数据与菜单数据的关联只能靠 `productName` ↔ 菜单 `name` 的名称模糊匹配（`src/matcher.py`）。注意名称差异：菜单名「麦咖啡™冰美式中杯」vs 营养表「冰美式中杯」；菜单名「纯牛奶(盒装)」vs 营养表「纯牛奶（盒装）」（全/半角括号）。

部分餐品有 nutritionDescription 趣味换算（如芝士安格斯厚牛堡=「能量约鲈鱼1条」、柠檬拉明顿=「能量约猕猴桃2个」）。

## 2. query-nearby-stores（门店）

入参：`{searchType:2, city:"深圳", keyword:"科技园", beType:1}`

返回 `data[]`：`{storeCode, storeName, address, distance(米), businessStatus, businessStartTime/EndTime, reservation, reservationTimeOptions[]}`

- beType=1（到店自提）→ 无 beCode，后续全链路不传 beCode（最简链路，本项目 MVP 采用）
- beType=5（得来速）→ 返回 beCode，后续必传
- 实测样例：`storeCode:"1420762"` 深圳同方信息港餐厅

## 3. query-meals（菜单）

入参：`{storeCode, orderType:1, beType:1}`（到店自取）

返回结构：
```
data.categories[]: [{name, meals:[{code, tags[]}]}]   # 分类索引
data.meals.{code}: {name, image, currentPrice(元,str), originalPrice(元,str),
                    discountType(null|"促销优惠"|"随单购麦金卡优惠"|...),
                    canWithOrder, withOrder{cardId,cardType,membershipCode,specId}}
```

关键实测：
- 单品短 code：巨无霸=1100、板烧鸡腿堡=1406、麦香鸡=1450、中薯条=4810
- 套餐长 code：990000xxxx（如 9900005466 巨无霸三件套 36.5 元 / 原价 49）
- **官方已有「500大卡套餐」分类**（9900011121/9900011126/9900011123/9900009245/9900009242）——控卡心智官方背书
- 「随心配 1+1」14.9/13.9 元——预算敏感场景的最优解候选
- 随单购麦金卡四件套 28~37 元（原价 55~66）——有麦金卡用户性价比极高

## 4. query-meal-detail（套餐组成 · 营养优化的黄金杠杆）

入参：`{storeCode, orderType:1, beType:1, code:"9900005466"}`

返回 `data.rounds[]`：每轮 `{id, name, quantity, minQuantity, maxQuantity, choices[]}`，choice 含 `{code, name, isDefault, diffPrice("+ ¥1"/"- ¥0.5"), supportModify, modification}`。

实测巨无霸三件套的三轮结构：
| 轮 | 默认 | 可换（营养视角） |
|---|---|---|
| 主堡 | 巨无霸 513kcal | — |
| 小食 | 中薯条 289kcal | 小杯玉米杯 53kcal 且 **-¥0.5**；迷你薯条 106kcal |
| 饮料 | 可乐中杯 147kcal | **无糖可乐中杯 0kcal 且 +¥0**；锡兰红茶 2kcal +¥1.5 |

→ **同价微调即可砍掉 ~380 kcal**，这是「精算」的核心卖点：不改店不改主食，只动配餐。

⚠️ modification（特调，selectedKey/unselectedKey 机制）对热量影响小且传参复杂，**MVP 不展开**（Skill 层注明「特调按默认处理」）。

## 5. query-store-coupons（门店可用券）

入参：`{storeCode, orderType:1, beType:1}`

返回 `data[]`：`{couponId, couponCode, title, tradeDateTime, products:[{productName, productCode}]}`。

实测当前账户返回 `[]`（无券）——**Skill 必须有无券兜底**：提示可调用 `auto-bind-coupons` 一键领券后重试。券的 `products[].productCode` 是营养表缺 code 问题的潜在补充数据源。

## 6. calculate-price（价格试算）

入参：`{storeCode, orderType:1, beType:1, items:[{productCode, quantity}]}`

返回（单位**分**）：
```
{productOriginalPrice, productPrice, originalPrice, discount, price,
 productList:[{productCode, productName, quantity, originalSubtotal, subtotal}],
 takeWayList:[{code:"eat-in"|"locker-out", title, subtitle}],
 enjoyed/enjoyable: {amountType(1特价/2折扣/3立减), realDiscount(元), balance}}
```

实测：巨无霸(2550) + 中薯条(1350) = 3900 分 = ¥39.0，discount=0。

## 对优化器设计的直接推论

1. 候选空间 = 单品组合（主食+小食+饮料）∪ 套餐（对每个套餐展开 round 替换变体）
2. 价格 = 单品 currentPrice 元；套餐 = currentPrice + Σ 替换 diffPrice（需解析 "+ ¥1" / "- ¥0.5" 字符串）
3. 名称匹配先标准化（去空格、统一括号、去™/【】装饰）再精确→子串→编辑距离三级降级
4. 600 限流下，一次完整精算 ≈ 4~6 次调用（门店1+菜单1+营养1+算价2~3），远低于限额
