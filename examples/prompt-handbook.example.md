---
title: "Codex 版 obsidian-llm-wiki 实战指令手册"
created: 2026-07-06
updated: 2026-09-13
domain: AI
tags: [AI/Obsidian, 工具/Obsidian/LLM-Wiki, 工具/编程工具/Codex, type/参考]
sources: []
status: active
---

#AI/Obsidian #工具/Obsidian/LLM-Wiki #工具/编程工具/Codex #type/参考

> 这是一份脱敏的公开实战手册范例。所有目录、页面和资料名称均与本仓库的初始化范例对应，可直接改成你自己的 vault 路径后使用。

## 与初始化范例配套使用

批量页面任务可延后共享文件同步：

```text
$obsidian-llm-wiki enhance-wiki-content --defer "wiki/<领域>/<页面>.md"
$obsidian-llm-wiki sync --dry-run
$obsidian-llm-wiki sync
```

不同页面可并行，同页必须串行。片段与锁是私人资料，不得提交。五种命令、跨运行时限制和恢复流程见 [defer/sync SOP](../references/defer-sync.md)。

建议先把以下文件复制到 Obsidian vault 根目录并重命名：

| 公开范例 | Vault 文件 | 用途 |
|---|---|---|
| [AGENTS.example.md](AGENTS.example.md) | `AGENTS.md` | 定义领域、目录、页面格式和安全规则 |
| [index.example.md](index.example.md) | `index.md` | 维护 wiki 页面目录与摘要 |
| [log.example.md](log.example.md) | `log.md` | 记录 append-only 操作日志 |

完整执行规则见 [SKILL.md](../SKILL.md)，更完整的 schema 参考见 [references/schema.md](../references/schema.md)。

本手册的示例路径与初始化范例保持一致：

| 领域 | raw 示例 | wiki 示例 |
|---|---|---|
| 读书笔记 | `raw/读书笔记/示例书籍/` | `wiki/读书笔记/示例书籍笔记.md` |
| AI | `raw/AI/示例 AI 工具课程/` | `wiki/AI/示例 AI 工具页面.md` |
| 项目资料 | `raw/项目资料/示例项目/` | `wiki/项目资料/示例项目复盘.md` |
| 提炼思维 | 无独立 raw 层 | `wiki/提炼思维/示例方法论.md` |

## 一、怎么写好指令

### 1.1 先说任务意图

一条好指令先说你要 Codex 做什么，再说明范围、写入边界和特殊要求。

| 意图 | 适合命令 | 重点说明 |
|---|---|---|
| 新资料入库 | `ingest` | raw 来源、目标领域、是否图片或文档密集 |
| 优化已有页面 | `优化 @wiki/...` | 保留什么、追加什么、是否读图 |
| 固定六类文末增强 | `enhance-wiki-content "<wiki页面>" ["<raw目录>"]` | 指定 raw 才读图；已有 frontmatter 与索引跳过 |
| 查询知识库 | `query` | 问题范围、希望引用哪些页面 |
| 只读评估 | `只读评估` | 不写文件，只给规模、风险和处理策略 |
| 提炼方法论 | `创建/优化提炼思维` | 来源页面、输出重点和复用场景 |
| 迁移旧笔记 | `migrate` | 来源位置、目标领域、是否先只做清单 |
| 清理页面 | `archive/remove/de-index/delete` | 优先归档或移出索引，明确是否真的删除文件 |

### 1.2 已内置规则，不必反复写

最新版 Skill 默认处理：

`enhance-wiki-content` 是以下自动修复规则的例外：已有 frontmatter（含 `updated`）和有效索引只验证，不修改；整块 frontmatter 缺失或页面未收录才补。Schema 与其他页面只检查。只给页面参数时不读图或 raw 内容。

- 检查并补齐 YAML frontmatter。
- 规范化 frontmatter tags 与 inline tags，标签片段中的空格会替换为 `_`。
- 每次执行都考虑 `AGENTS.md`、`CLAUDE.md`、`index.md` 是否需要更新，并按 vault 声明处理两个 schema 入口的关系。
- `index.md` 同时维护 `indexed_page_count`、`wiki_file_count`、`registered_domain_count`，以及 `missing_count`、`broken_count`、`duplicate_count`。
- 已有 wiki 文件第一次补录进 `index.md` 时按 `补录既有页面 / first-time index backfill` 处理；统计漂移时重新计算全部六项变量，不在旧数字上盲目递增。
- 有文件变更时按规则追加 `log.md`；大日志只读取末尾 80 行，必要时最多 200 行，并通过唯一 EOF 锚点、`apply_patch` 和旧内容前缀哈希验证 append-only。
- `raw/` 只读，不移动、不修改、不删除。
- 优化页面时保留已有 wiki 链接和 `![[图片.png]]` 嵌入。

你通常只需要补充：

- 是否只读。
- 是否保留现有正文和结构。
- 新内容放在哪个章节或是否放在 `## 相关` 前。
- 是否分析全部图片。
- 是否允许 default agents 分批读图。
- 是否允许生成或保存中间产物。

### 1.3 文档预处理与图片理解分工

| 任务 | 推荐方式 | 说明 |
|---|---|---|
| PDF/DOCX/PPTX/XLSX 文本、页序、slide 顺序和内嵌图片 | 项目 `.venv` | 做确定性预处理和 manifest |
| 截图文字、流程图、课件图和界面图理解 | default agents | 做 OCR-like 阅读、视觉理解和洞见提炼 |
| 大量图片分批 | 主 Codex 调度 default agents | 最多 6 个总批次；并发不足时分波执行 |
| 最终 wiki 写入 | 主 Codex | 统一格式、顺序、链接、索引和日志 |

default agents 不是传统 OCR。它们更适合“可见文字读取 + 图表/流程/UI 理解 + 内容提炼”。

## 二、基础命令

| 命令 | 用途 |
|---|---|
| `ingest <source>` | 摄入 raw 新来源并创建或更新 wiki 页面 |
| `enhance-wiki-content "<wiki页面>" ["<raw目录>"]` | 保留原文及媒体，在 EOF 增补六类内容；可选 raw 图片来源 |
| `query <问题>` | 基于现有 wiki 综合回答问题 |
| `lint` / `audit` | 检查 frontmatter、链接、sources、孤立页面和索引 |
| `index` | 重建或刷新知识库索引 |
| `migrate` | 把旧笔记迁入 LLM Wiki 结构 |
| `archive/remove/de-index/delete` | 归档、移出索引或谨慎删除 wiki 页面 |

## 三、高频模板

### 3.1 Ingest 新来源

普通资料目录：

```text
$obsidian-llm-wiki ingest @raw/读书笔记/示例书籍/，整理为 @wiki/读书笔记/示例书籍笔记.md，并提炼核心观点、方法论、最佳实践和相关页面。
```

截图课程或图片目录：

```text
$obsidian-llm-wiki ingest @raw/AI/示例 AI 工具课程/，这是截图课程资料。按自然文件名顺序建立 image manifest；图片较多时调用 default agents 分批只读分析，输出课程结构、图片内容解析、核心观点、洞见、方法论和最佳实践。
```

### 3.2 优化已有页面

固定六类文末增强，读取指定目录中的图片：

```text
$obsidian-llm-wiki enhance-wiki-content "wiki/AI/示例 AI 工具页面.md" "raw/AI/示例 AI 工具课程/"
```

固定六类文末增强，只依据原正文，不读图：

```text
$obsidian-llm-wiki enhance-wiki-content "wiki/项目资料/示例项目复盘.md"
```

两种形式都在原 EOF 后追加 **资料总结、洞见、方法论提炼、最佳实践、金句精选、关联 Wiki**。页面和指定的 raw 目录必须真实存在且位于当前 vault 对应层内；无效参数零写入。含空格的路径必须加引号；本例名称是虚构名称，使用前替换为你的既有页面和目录。

保留原正文、链接、图片与视频等媒体引用及顺序，不改路径、不插入媒体。指定 raw 时先建立有序 image manifest，对账后分析；未指定时即使有图片和 `sources` 也只读正文。无法识别的图片明确报告，不凭文件名补写内容；视频、音频不默认播放或转录。

已有 frontmatter 全部保持原样，包括 `updated`；整块缺失才在顶部补齐，字段缺口只报告，无法安全解析时停止写入。已有有效索引保持整份索引不动；确认未收录才补录该页并重算六变量。关联 Wiki 须真实存在，金句区分摘录与提炼；重复调用不重复堆叠已有内容。实际变更后只追加一次日志，无变化不改日期、不写日志。

真实页面、图片、提炼内容、manifest 和测试库仅留在本地，不复制到公开仓库或 PR 描述。

允许整理页面结构：

```text
$obsidian-llm-wiki 优化 @wiki/读书笔记/示例书籍笔记.md，读取 declared sources，保留已有图片嵌入和顺序；补充资料总结、洞见、方法论提炼、最佳实践和金句精选。
```

只追加、不改原文：

```text
$obsidian-llm-wiki 优化 @wiki/项目资料/示例项目复盘.md，只追加总结和洞见到 ## 相关 前；不修改现有正文、图片嵌入和顺序。
```

### 3.3 PDF / DOCX / PPTX / XLSX

```text
$obsidian-llm-wiki ingest @raw/项目资料/示例项目/项目复盘.pptx，先用项目 .venv 提取文本、元数据、slide 顺序和图片 manifest；必要时再用 default agents 分批读图，最终整理为 @wiki/项目资料/示例项目复盘.md。
```

中文 PDF 使用固定预处理脚本，并在交付完成后清理本次任务目录：

```text
$obsidian-llm-wiki ingest @raw/项目资料/示例项目/示例报告.pdf，先用固定 preprocess_pdf.py 提取逐页文本、页码、元数据和图片 manifest，检测乱码并渲染异常页；完成 wiki、索引和验证后，依据 created_files.json 逐项清理本次 tmp/obsidian-llm-wiki/<task-id>/，不要处理其他任务目录。
```

清理时必须逐文件、逐空目录执行，不得使用递归、通配符、循环、管道或批量删除。执行策略阻止空目录删除时，保留空目录并报告受控残留。

只做预处理评估：

```text
$obsidian-llm-wiki 只读评估 @raw/项目资料/示例项目/项目复盘.pptx，不修改任何文件；报告可提取文本、页数、图片数量、处理风险和建议工作流。
```

### 3.4 大量图片与 default agents

```text
$obsidian-llm-wiki 优化 @wiki/AI/示例 AI 工具页面.md，分析 @raw/AI/示例 AI 工具课程/ 中的全部图片。先建立 image manifest，核对顺序、缺失和重名；拆成不超过 6 个总批次，并按可用并发槽分波调用 default agents 只读分析，由主 Codex 核对覆盖率并统一整合。
```

要求每张图片返回固定字段：

```text
$obsidian-llm-wiki 针对 @wiki/AI/示例 AI 工具页面.md 的图片做批量只读分析。每张图返回 manifest index、文件名、可见文字、主题、关键要点、图表或 UI 元素、洞见、置信度和无法识别内容；主 Codex 最后输出批次摘要并检查是否漏图。
```

### 3.5 Query

```text
$obsidian-llm-wiki query 这个知识库中关于 AI 工具应用与项目复盘有哪些可复用方法？请综合 [[示例 AI 工具页面]] 和 [[示例项目复盘]] 回答，并标明来源页面。
```

### 3.6 只读评估

```text
$obsidian-llm-wiki 只读评估 @raw/AI/示例 AI 工具课程/ 和 @wiki/AI/示例 AI 工具页面.md：不修改任何文件；统计文档和图片数量，检查 sources 与图片引用，判断是否需要 .venv、image manifest 或 default agents，并给出建议流程。
```

### 3.7 提炼思维

```text
$obsidian-llm-wiki 根据 [[示例书籍笔记]]、[[示例 AI 工具页面]] 和 [[示例项目复盘]]，创建 @wiki/提炼思维/示例方法论.md，提炼可复用模式、执行步骤、最佳实践、避坑指南和适用边界。
```

扩充已有方法论：

```text
$obsidian-llm-wiki 优化追加 @wiki/提炼思维/示例方法论.md，保留原有结构，把新洞见放进合适章节，并补充来源页面链接。
```

### 3.8 Lint / Audit / Index

```text
$obsidian-llm-wiki lint，检查 wiki 页面 frontmatter、inline tags、sources、图片引用、孤立页面、重复索引和失效链接；先报告问题，不自动修复。
```

```text
$obsidian-llm-wiki index，按 vault schema 的领域注册表刷新 index.md，检查页面摘要、标签和路径，并重新计算三项权威变量与三项健康变量。
```

补录既有页面：

```text
$obsidian-llm-wiki index，检查 @wiki/项目资料/示例项目复盘.md 是否已收录进 index.md；如果文件存在但尚未收录，请作为补录既有页面加入索引，并刷新三项权威变量、三项健康变量、footer 和索引健康行。
```

### 3.9 Migrate

先只读规划：

```text
$obsidian-llm-wiki migrate @旧笔记目录/，先只读评估可迁移页面、目标领域、重名和链接风险，输出迁移清单后停止。
```

明确执行目标：

```text
$obsidian-llm-wiki migrate @旧笔记目录/示例项目复盘.md 到 @wiki/项目资料/示例项目复盘.md，保留原文，补齐摘要、frontmatter、相关链接和来源；不要移动或删除 raw/。
```

### 3.10 Archive / Remove / De-index / Delete

优先移出索引：

```text
$obsidian-llm-wiki 将 @wiki/项目资料/示例项目复盘.md 从 index.md 中移出，但保留文件；检查相关链接和影响范围。
```

归档页面：

```text
$obsidian-llm-wiki 归档 @wiki/项目资料/示例项目复盘.md，保留文件并将 status 改为 archived；检查索引和相关页面是否需要调整。
```

只有确定要物理删除时才使用：

```text
$obsidian-llm-wiki 删除 @wiki/项目资料/示例项目复盘.md。只处理这一份明确的 wiki 文件，不删除 raw/；删除前报告影响范围。
```

### 3.11 Log 状态、查询与分卷

只读查看活动日志大小、日期范围和轮转状态：

```text
$obsidian-llm-wiki log status
```

查询活动日志和历史分卷：

```text
$obsidian-llm-wiki log query "YYYY-MM-DD optimize"
```

显式轮转：

```text
$obsidian-llm-wiki log rotate now
$obsidian-llm-wiki log rotate year
$obsidian-llm-wiki log rotate size
$obsidian-llm-wiki log rotate auto
```

写入型任务会在最终追加日志前自动运行低Token预检；query、只读audit、`log status`和`log query`不会自动轮转。默认在投影大小达到2 MiB或活动日志跨年时整卷归档。分卷只是整理，不是独立备份。

## 四、命令决策树

```text
你要做什么？
│
├─ 有新资料要处理
│   ├─ 普通 raw 文档 → ingest
│   ├─ PDF/DOCX/PPTX/XLSX → ingest + 文档预处理
│   └─ 截图课程/大量图片 → ingest + image manifest
│
├─ 已有页面需要优化
│   ├─ 可以整理结构 → 优化 @wiki/页面
│   └─ 不改原文 → 只追加内容到 ## 相关 前
│
├─ 图片很多
│   ├─ 先建立 image manifest
│   ├─ 核对顺序、缺失和重名
│   └─ 最多 6 个总批次，并按可用并发槽分波只读分析
│
├─ 只想评估 → 只读评估
├─ 提炼跨页面方法论 → 创建或优化提炼思维
├─ 搬迁旧笔记 → migrate，先清单后执行
├─ 清理页面 → 优先 de-index 或 archived
├─ 检查或追溯日志 → log status / log query
├─ 手动整理活动日志 → log rotate now / year / size / auto
└─ 维护知识库 → query / lint / audit / index
```

## 五、最佳实践

- **说清目标**：不要把 ingest、优化、迁移和删除混在一个模糊请求里。
- **说清范围**：给出具体 `@raw/...` 或 `@wiki/...` 路径。
- **说清写入边界**：只读、不改原文、只追加、允许重构、允许归档或删除。
- **图片先建 manifest**：图片密集资料先明确顺序和覆盖范围。
- **文档先预处理**：PDF/DOCX/PPTX/XLSX 先做确定性解析，再决定是否读图。
- **主 Codex 统一收口**：default agents 只做只读分析，主 Codex 负责覆盖率、整合和写入。
- **日志预检无需重复描述**：写入型任务会自动调用固定脚本；只有显式查询或轮转时才使用 `log` 命令。
- **特殊要求才写出来**：例如只处理前 30 张图、不要调用 default agents、只报告差异。

## 六、常见避坑

- 不要把 default agents 当成纯 OCR；它们还负责图表、流程、界面和上下文理解。
- 不要只写“读取全部图片”，应同时说明顺序、缺失、重名和低置信度处理要求。
- 不要要求中间产物默认写入 `raw/`；`raw/` 是不可变来源层。
- 不要在每条提示词中重复 frontmatter、索引和日志规则；这些属于 Skill 默认职责。
- 不要把分卷当作备份，也不要要求 Skill 自动删除、压缩或合并历史卷。
- 不要直接物理删除 wiki 页面；大多数清理任务更适合归档或移出索引。

## 相关资源

- [项目 README](../README.md)
- [Codex Skill](../SKILL.md)
- [AGENTS 初始化范例](AGENTS.example.md)
- [index 初始化范例](index.example.md)
- [log 初始化范例](log.example.md)
- [完整 schema 参考](../references/schema.md)
