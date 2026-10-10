# 📣 推广 Playbook（搁置友好版：全部一次性准备好，想发时复制粘贴）

> 设计原则：**不需要持续投入**。A 组已由 WorkBuddy 自动完成（永久生效）；B 组是 5 分钟级"复制粘贴"动作，做不做随缘；每组文案已写好。
> 背景：比赛 2026-10-25 23:59 截止，排名按 GitHub Star 数。任何渠道引来的 Star 都有效。

---

## A 组：已自动完成（零维护，永久生效）✅

| 动作 | 状态 | 说明 |
|---|---|---|
| GitHub description（<120 字符含关键词） | ✅ | "AI meal actuary for McDonald's China via official MCP..."，GitHub 站内搜索 + Google 均可命中 |
| 12 个 topics | ✅ | mcp / mcdonalds / nutrition / calorie-counter / ai-agent / workbuddy / llm / meal-planner / health / fast-food / optimization / china —— topic 页是 GitHub 站内长尾流量的主要入口 |
| README 英文摘要段 | ✅ | GEO 核心：让英文查询（Google / ChatGPT / Perplexity）能索引到本项目 |
| 结构化对比表（vs 竞品） | ✅（首日已有） | LLM 生成回答时最爱引用的结构化素材，GEO 的核心弹药 |
| MIT License / 完整 README | ✅ | 转化率基础盘 |

**GEO 说明（诚实版）**：MCP 目录站（Smithery / glama.ai / PulseMCP / mcp.so）收录的对象是 MCP **Server**，本项目是跑在客户端侧的 **Skill**，投了会被拒——"麦当劳 MCP"这类查询的流量主要被官方 mcd-mcp-server 仓库吃掉，我们蹭不到，不硬蹭。本项目可被 GEO 引用的真实抓手就是：README 的英文段 + 对比表 + 数据表格，这些正是生成引擎引用时偏好引用的结构化内容。

---

## B 组：复制粘贴动作（每个 ≤5 分钟，按性价比排序）

### B1. V2EX「分享创造」节点（最推荐——唯一无需养号的中文技术社区）

V2EX 分享创造节点明确允许自推广，对"麦当劳 MCP 赛博整活"题材接受度高。

**标题**：
```
麦麦营养精算师：用麦当劳官方 MCP 写了个“40 块钱吃 25g 蛋白还不超过 600 大卡”的精算器
```

**正文**（直接粘贴）：
```
起因：麦当劳中国开放了官方 MCP（mcd-mcp-server），2026 程序员节办了个开发大赛，排名按 GitHub Star 数。

我用周末时间写了个 Skill 叫「麦麦营养精算师」，思路很简单：
营养数据官方已经给全了（160 个餐品的热量/蛋白/钠/钙），我只需要做组合枚举。

输入：预算 ≤40 元、热量 ≤600 kcal、蛋白 ≥25g
输出：Top3 套餐方案，每个方案带实付价（走 calculate-price 实时复核）、完整营养表、
以及"吃完要跑几公里"换算。

最好玩的一个发现：套餐内同价微调可以砍掉几百大卡——
中薯条换小杯玉米杯：-236 kcal 还便宜 5 毛；
可乐换无糖可乐：-147 kcal 不加钱。

架构上刻意省算力：LLM 只负责调 MCP 拽数据，组合精算交给本地确定性引擎
（纯标准库、零第三方依赖、15 个单测），一次精算 ≤8 次 MCP 调用。
反正枚举和差价解析这种确定性计算让 LLM 心算又贵又容易错。

仓库（求个 Star，比赛按 Star 排名 🙏）：
https://github.com/kaitoops/mcd-nutrition-actuary

欢迎轻喷，特别是营养学方面的批评。
```

### B2. Reddit r/SideProject + r/coolgithubprojects（英文，两天各发一次，不要同天）

**Title**:
```
I built an AI meal actuary for McDonald's China: give it a budget + calorie cap + protein floor, it exhaustively searches ~10k menu combos for the best meal
```

**Body**:
```
McDonald's China opened up an official MCP server (their API for AI agents), so I built a skill on top of it: McNutrition Actuary.

You say "¥40, under 600 kcal, at least 25g protein" — it enumerates the full menu combinations and returns the top 3 meal plans, each with live checkout pricing (real API, not menu-list prices), full nutrition facts, and a "how many km you need to run" conversion.

The fun part: same-price swaps that cut hundreds of calories. Medium fries → corn cup is −236 kcal AND ¥0.5 cheaper. Regular Coke → Coke Zero is −147 kcal for free. Nobody orders these because nobody sees the numbers side by side.

Design choice I'm happy with: the LLM only orchestrates MCP data fetching; all the combinatorics runs in a deterministic local optimizer (pure stdlib, 15 unit tests, zero dependencies). One consultation = ≤8 MCP calls. Deterministic math is not a job for LLM mental arithmetic.

Repo: https://github.com/kaitoops/mcd-nutrition-actuary

It's an entry for a McDonald's China dev challenge ranked by GitHub stars, so if you find it fun, a star helps. Roast the nutrition science if you want — that part I'm least sure about.
```

> 提示：r/SideProject 明确允许自推广；r/coolgithubprojects 就是专为 GitHub 项目设的。两个都发但**隔 48 小时**，别同天。

### B3. Hacker News「Show HN」（天花板最高，条件也最苛刻）

**前提自查**：需要有一定 karma 的账号（新号/零 karma 容易被压）。没有就跳过，B1/B2 够用。

**时机**：美东周二–周四早 8–10 点 = **北京时间周二–周四 20–22 点**。建议窗口：**10-13（周二）或 10-14（周三）晚**，留足发酵期到 10-25 截止。

**Title**:
```
Show HN: McNutrition Actuary – AI that finds the best McDonald's meal for your macros
```

**首评（发出后 5 分钟内自己回）**：
```
Author here. McDonald's China ships an official MCP server (menu, nutrition, store, pricing APIs for AI agents), and this is a skill built on it.

Why it exists: the nutrition data was all there (160 items, full macros), but no tool was using it for decision-making. So the interesting part isn't data access — it's the optimizer: a constraint-filtered enumeration (~10k candidates) with a multi-objective score, entirely deterministic, zero LLM math. The LLM's job is only to translate a vague request into constraints and fetch MCP data; one consultation costs ≤8 API calls.

The result I like most: it surfaced same-price swaps nobody would spot manually — medium fries → small corn cup is −236 kcal and half a yuan cheaper.

Stack: pure Python stdlib, 15 tests, no deps. Happy to answer questions about the optimizer or the MCP integration.
```

> HN 铁律：用同行口吻，零营销腔；前 1 小时每评必回；被质疑营养学就诚实认。

### B4. X/Twitter（一条，带 README 截图或精算报告截图）

```
McDonald's China has an official MCP server for AI agents, so I built an actuary on top of it:

"¥40, ≤600 kcal, ≥25g protein" → exhaustive search over ~10k menu combos → top 3 meals with live prices.

Same-price swap found: fries → corn cup = −236 kcal AND cheaper.

https://github.com/kaitoops/mcd-nutrition-actuary
```

### B5. dev.to 文章（可选，长期 SEO 价值最高的一步）

标题套用高意图检索式：**"I built a nutrition optimizer on McDonald's official MCP server (with a deterministic LLM-orchestration pattern)"**。标签 `#showdev #python #ai #mcp`。内容三段：问题（营养数据齐但没人用）→ 架构（LLM 编排 + 确定性引擎，为什么不让 LLM 算数）→ 踩坑（营养表无 productCode 的名称匹配、价格单位是分、早餐时段菜单切换）。文章末尾放仓库链接。这篇写一次能吃几年搜索长尾——但也是最花时间的选项，搁置期可不做。

---

## 执行清单（总投入 ≈ 15 分钟的版本）

```
[ ] B1 V2EX（今天，5 分钟）
[ ] B2 r/SideProject（今天或明天，3 分钟）；r/coolgithubprojects（+48h）
[ ] B4 X 一条（顺手，2 分钟）
[ ] B3 Show HN（可选：有 karma 账号才做，周二/三晚 8-10 点）
```

**Star 之后会发生什么**：GitHub 推荐算法对 star 增速敏感；若 24h 内到 50+，有概率进 GitHub Trending（Python 或"周榜"），那是免费的长尾放大器——但这些不可控，发了就算完成动作。
