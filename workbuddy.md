# workbuddy.md — 本项目由 WorkBuddy 全程辅助开发

> 本文件为 2026 麦当劳程序员创意开发大赛「使用 WorkBuddy 开发」专项奖励的提交凭证，
> 记录 WorkBuddy 在本项目开发全流程中的实际参与过程。
> 涉及凭证处已脱敏为 `Bearer YOUR_MCP_TOKEN`。

## 开发环境

- **AI 助手**: WorkBuddy（GLM 驱动桌面 Agent）
- **MCP 客户端**: WorkBuddy 内置 MCP 连接器（`mcd-mcp`，endpoint `https://mcp.mcd.cn`）
- **开发周期**: 2026-10-10（单日完成从情报收集到推送 GitHub 的完整 MVP）
- **人机分工**: 人类负责决策拍板、Token 申请、GitHub 仓库创建；WorkBuddy 负责其余全部（调研/配置/编码/测试/文档/git）

## 开发过程实录

### Phase 1 — 情报收集与方向决策

WorkBuddy 通过 Web 检索与抓取完成赛前尽调：

1. 定位官方组织 `M-China`，找到 `mcd-developer-innovation-challenge`（赛事规则）与 `mcd-mcp-server`（MCP 接入指南）两个仓库
2. 提取关键赛制情报：**排名以 GitHub Star 数为准**、Issue 正文 ≤1000 字、`CONTEST_DECLARATION.md` 内容不可改、`workbuddy.md` 是 3000 积分专项奖励的必要文件、MCP 限流 600 次/分钟
3. 扫描竞品格局：省钱凑单赛道已有完整竞品（麦门精算师），**营养赛道为蓝海**
4. 基于上述情报给出方向建议矩阵（省钱/卡路里/营养搭配三维度 × 竞品/算力/传播性评估），人类拍板：

> **决策：三方向合并为「营养+预算精算师」——预算×热量×蛋白多约束下的最优套餐搭配，避开省钱红海，主打"同价微调砍掉几百大卡"**

### Phase 2 — MCP 能力实测探测（7/7 工具打通）

人类在 open.mcd.cn/mcp 申请 Token（WorkBuddy 给出逐步指引），WorkBuddy 将其合入 WorkBuddy MCP 配置（`Authorization: Bearer YOUR_MCP_TOKEN`，脱敏），并实测 7 个关键工具的真实返回结构：

| 工具 | 探测发现（成为后续设计依据） |
|---|---|
| `list-nutrition-foods` | 160 餐品 × 9 营养字段（kJ/kcal/蛋白/脂肪/碳水/钠/钙）；**无 productCode，与菜单只能按名称匹配** |
| `query-nearby-stores` | 拿到深圳真实门店 storeCode |
| `query-meals` | 菜单分类结构清晰；**官方自带「500大卡套餐」分类与随心配 1+1**——控卡心智有官方背书 |
| `query-meal-detail` | 套餐内 round 级可替换结构 + diffPrice：中薯条→玉米杯 -236kcal 还便宜 0.5 元——**本项目核心卖点来源** |
| `calculate-price` | 价格单位为**分**，需 /100 转元 |
| `query-store-coupons` | 券结构完整，但账户可能无券 → Skill 必须设计无券兜底 |
| `now-time-info` | 营业时间判断 |

全部发现沉淀为 `docs/api-notes.md` 数据契约笔记。

### Phase 3 — 核心算法开发（WorkBuddy 编码 + 自测自修）

WorkBuddy 编写零第三方依赖的精算引擎并跑测试迭代：

- `src/optimizer.py`：多约束组合枚举（约 1 万候选精确枚举）+ 多目标评分 + **Top3 主食互异多样性约束**
- `src/matcher.py`：营养表名称三级匹配（别名表 / 标准化 / 子串），弥合"营养表无 productCode"缺口
- `tests/test_optimizer.py`：15 个用例

**WorkBuddy 自主发现并修复的 3 个 bug**（首轮 15 测 12 过，根因分析后三连修，复测 15/15）：

1. 「那么大鸡排」被 side 正则抢分类（385kcal/24g 蛋白实为主食级）→ 调整分类优先级
2. 测试断言把 kJ 当 kcal（冰美式 54kJ ≈ 13kcal，黑咖啡本就低热量）→ 修正断言
3. 省钱党 20 元场景无解：根因是「麦香鸡」不在主食正则 → 补全后自然可解

另修复**多样性约束失效**（Top3 出现重复主食）——`main_names()` 误用全部 items 集合，修正后 Top3 主食互异且热量分布更优。

### Phase 4 — Skill 编排层设计

关键架构决策由 WorkBuddy 提出（契合「省算力」目标与确定性原则）：

> **AI 只做数据搬运，组合精算交给确定性 CLI。** 枚举与差价解析是确定性计算，LLM 心算易错且贵；代码一次写好永久零边际成本。单次精算 ≤8 次 MCP 调用。

产出：`skill/SKILL.md`（编排文档）+ `scripts/actuary_cli.py`（JSON 进 → 报告出）。

### Phase 5 — 参赛三件套与发布

WorkBuddy 抓取官方 `CONTEST_DECLARATION.md` **原样落盘**（一字不改），撰写 README（含与竞品差异化对比表）与 MCP_INTEGRATION.md，初始化 git 并提交（`24b0981`，17 文件 1456 行）。推送时 HTTPS 直连被重置，WorkBuddy 诊断后切换 SSH 通道完成推送。

## WorkBuddy 价值总结

| 环节 | 人类 | WorkBuddy |
|---|---|---|
| 赛制/竞品情报 | — | ✅ 全部 |
| 项目方向 | 拍板（30 秒） | ✅ 备选矩阵与论据 |
| MCP Token | 申请+粘贴 | ✅ 配置+验证+7 工具探测 |
| 编码/测试/修 bug | — | ✅ 全部（15/15 测试） |
| 参赛文档 | — | ✅ 全部 |
| git/推送 | 建空仓库 | ✅ 提交+排障+推送 |
| GitHub 仓库创建 | ✅（2 分钟） | — |

**结论**：人类总投入 ≈ 10 分钟手动操作，其余由 WorkBuddy 在单日会话内完成——典型的「一个人 + AI 系统」超轻量参赛工作流。
