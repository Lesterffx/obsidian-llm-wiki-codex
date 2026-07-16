# AGENTS.md / CLAUDE.md 通用模式模板

> 新 Obsidian vault 优先使用 `AGENTS.md` 作为 Codex schema；如需兼容 Claude Code，可同步保留同内容的 `CLAUDE.md`。Codex 执行时优先读取 `AGENTS.md`，缺失时再读取 `CLAUDE.md`。

```markdown
# <Vault 名称> — LLM Wiki Schema

## 角色

你是这个知识库的维护者。你的职责是处理原始资料、维护结构化 wiki、回答问题、保持知识库健康。你负责编写和维护 wiki 页面；人类负责策划原始资料、提出问题、引导方向。

## 架构

三层结构：

- **raw/** — 不可变原始资料。只读。绝不修改、移动或删除 raw/ 下的文件。
  - 附件（图片）按领域分散在各 raw/ 子目录中，与源资料同目录。
  - `raw/<领域1>/` — <领域1> 的源资料和附件。
  - `raw/<领域2>/` — <领域2> 的源资料和附件。
- **wiki/** — LLM 生成和维护的 wiki 内容。这是可写层。
  - `wiki/<领域1>/` — <领域1> 的知识页面。
  - `wiki/<领域2>/` — <领域2> 的知识页面。
- **AGENTS.md** — Codex 优先读取的项目 schema。
- **CLAUDE.md** — Claude Code 兼容 schema（可选）。
- **index.md** — 内容目录（LLM 维护）。
- **log.md** — 操作日志（append-only）。

## 领域注册表

| 领域 | raw 路径 | wiki 路径 | 描述 |
|---|---|---|---|
| <领域1> | raw/<领域1>/ | wiki/<领域1>/ | <描述> |
| <领域2> | raw/<领域2>/ | wiki/<领域2>/ | <描述> |

新增领域：创建 `raw/<名>/` + `wiki/<名>/`，并在本表添加一行。若无 raw 层，在 raw 路径中写 `—`。

## 命名约定

- 文件名：中文描述性标题，与页面标题一致。
- 日期前缀仅用于时序条目：`2026-04-10 会议主题.md`。
- 一个文件一个概念，倾向拆分而非堆叠。

## Frontmatter 规范

每个 wiki 页面必须从第一行开始写 YAML frontmatter，以 `---` 开头：

\```yaml
---
title: "页面标题"
created: YYYY-MM-DD
updated: YYYY-MM-DD
domain: <领域名>
tags: [type/book, AI/编程]
sources: []
status: draft | active | archived
---
\```

新增、修改、查询、迁移、索引、审计或优化任何 wiki 页面时，必须先检查 YAML frontmatter 是否存在且字段完整。若不存在、位置不在文件第一行、或字段缺失，默认必须在正文前补齐/修复上述笔记属性，并在内容、标签或来源元数据发生变化时更新 `updated`。

YAML frontmatter 属于结构维护例外。用户要求“append-only”“补充放最后”“不修改现有正文/顺序”时，这些限制只约束正文、图片、链接和补充章节，不阻止把 frontmatter 补到页面顶部。只有用户明确说“只读”“审计-only”“不要修改任何文件”时，才只报告缺口不写入。

## 标签体系

| 类别 | 模式 | 示例 |
|---|---|---|
| 类型 | `type/<类别>` | `type/book`, `type/会议`, `type/工具` |
| <自定义> | `<前缀>/<主题>` | `AI/编程`, `工具/编程工具/Codex` |

Frontmatter 的 `tags` 字段是权威来源。如果存在 inline tags，应与 frontmatter 匹配。

### 标签规范化

- 标签只在 frontmatter `tags` 与 inline `#tag` 中规范化，不自动改 `domain`、`sources`、raw/wiki 路径、目录名、文件名、页面标题、wiki 链接、图片嵌入或正文普通文本。
- 标签片段中如有空白，统一用 `_` 连接。例如：`AI Live` → `AI_Live`，`domain/AI Live` → `domain/AI_Live`。
- Inline tags 必须与规范化后的 frontmatter `tags` 保持一致。

## Wiki 链接

- 使用 `[[页面标题]]` 链接相关页面。
- 首次提到值得拥有独立页面的概念时创建链接。
- 每个页面应链接到至少 2 个其他页面。
- 使用 `![[文件名]]` 引用 raw/ 子目录中的图片。

## 图片管理

- 图片按领域分散在 raw/ 子目录中，与源资料同目录。
- 优化或重构 wiki 页面时，绝不删除已有 `![[图片.png]]` 嵌入。
- 遇到图片密集页面或 raw 图片目录时，先建立 image manifest，再决定读取与分批策略。
- wiki 页面已有 `![[...]]` 嵌入顺序是权威顺序；raw-only 图片目录按自然文件名顺序处理。
- 图片重名、缺失、无法唯一定位、或不在 declared `sources` 中时，必须先报告，不猜测。

### 图片密集资料处理

- 适用于截图课程、PPT 截图、raw 图片目录、wiki 页面图片嵌入、以及 PDF/DOCX/PPTX 中抽取出的页面或图片。
- 主 Codex 负责建立 manifest、分批、校验覆盖率、整合分析结果和最终写入 wiki。
- 图片少量时可由主 Codex 直接读取分析；图片较多时可调用内置 `default` agent 并行分析。
- `default` agents 只读图片并返回分析结果，不修改 `raw/`、`wiki/`、`index.md`、`log.md` 或 schema 文件。
- 最多并行 6 个 default agent 批次；100 张以上图片先拆成最多 6 个批次，必要时再继续分批。

### 文档预处理运行时

- 如果项目存在 `.venv`，优先使用项目内 Python：

\```powershell
& ".\.venv\Scripts\python.exe" ".\scripts\<script>.py" "<input-path>" "<output-path>"
\```

- PDF/DOCX/PPTX/XLSX 等文档先用 `.venv` 做确定性预处理：提取文本、元数据、内嵌图片、页序、slide/page 顺序和 manifest。
- `.venv` 负责可重复的解析、排序、抽取和 manifest；`default` agents 负责 OCR-like 图片阅读、截图理解、图表理解和洞见提炼。
- 不默认假设 Tesseract、OpenCV、PaddleOCR、RapidOCR 等传统 OCR 引擎可用。

## 页面结构

1. YAML frontmatter（文件第一行，以 `---` 开头）
2. Inline tags（兼容 tag-wrangler 插件）
3. 一句话摘要（以 `>` 引用格式）
4. 正文内容
5. `## 相关` — wiki 链接到相关页面
6. `## 来源` — 引用 raw 来源

## 变更联动

任何一次 LLM Wiki 操作（ingest、query、lint、migrate、index、delete/remove、optimize、提炼思维等）都必须执行强制维护检查：主动检查 `AGENTS.md`、`CLAUDE.md`、`index.md` 和任务相关 wiki 页 frontmatter 是否保持最新。可以检查后不修改，但必须纳入判断；若发现结构缺口，默认修复。显式只读/审计/no-write 请求优先，此时只报告缺口。

每次创建或修改 wiki 页面后，必须级联执行以下操作：

| 操作 | 触发条件 | 说明 |
|---|---|---|
| 检查/更新 `AGENTS.md` | 任何 LLM Wiki 操作 | 检查领域注册表、raw/wiki 路径、处理规则、安全规则、标签规则是否需要更新 |
| 检查/更新 `CLAUDE.md` | 任何 LLM Wiki 操作 | 检查是否需要与 `AGENTS.md` 的共享 schema 保持兼容同步 |
| 检查/更新 `index.md` | 任何 LLM Wiki 操作；页面新增、删除、迁移、标签或摘要变化时通常需要更新 | 注册新页面、补录既有页面、更新摘要、移除或修正旧条目；修改前同时计算 `indexed_page_count`、`wiki_file_count` 和 footer count |
| 追加 `log.md` | 任何 wiki 变更 | 记录操作类型、变更内容、影响范围 |
| 更新 `sources` | 新建页面 / 发现来源为空 | 指向对应的 raw 目录或文件 |
| 更新相关 wiki 页面 | 新内容影响已有页面 | 交叉引用、修正矛盾、补充新信息 |

### index.md 数量规则

- 修改 `index.md` 前，先计算两个数量：`indexed_page_count`（已收录进 `index.md` 的唯一 wiki Markdown 页面数）和 `wiki_file_count`（扫描 `wiki/**/*.md` 得到的实际文件数）。
- 底部 `_统计：N 个页面 | M 个领域 | 上次更新于 YYYY-MM-DD_` 中的页面数以 `indexed_page_count` 为准；`wiki_file_count` 只用于覆盖率、漏收录、断链和重复条目检查。
- 如果既有 wiki 文件首次补录进 `index.md`，按 `补录既有页面` / `first-time index backfill` 处理：footer 与补录前 `indexed_page_count` 一致时页面数 +1；若 footer 已漂移，则修正为补录后的 `indexed_page_count`。
- 如果页面已在 `index.md`，只是摘要、标签、路径或章节位置变化，不修改 page count 数字；可以按需刷新顶部维护说明和底部日期。
- 如果 `indexed_page_count` 与 footer 既有数量不一致，视为统计漂移，修正为 `indexed_page_count`，并在 `log.md` 记录 `统计漂移修正`。

### log.md 格式

\```markdown
## [YYYY-MM-DD] <操作类型> | <标题>

- 页面：`wiki/<路径>.md`
- 操作：<操作描述>
- 变更：
  - 具体变更 1
  - 具体变更 2
- `AGENTS.md`：已检查 / 已更新 / 无需更新，xxx
- `CLAUDE.md`：已检查 / 已更新 / 无需更新，xxx
- `index.md`：已检查 / 已更新 / 无需更新，xxx
- frontmatter：已检查 / 已补到顶部 / 已修复字段 / 只读未写入，xxx
- index 数量：`wiki_file_count` = N；`indexed_page_count` = M；footer count = K；已变化 / 未变化 / 已修正统计漂移，xxx
\```

操作类型：`ingest` | `optimize` | `lint` | `audit` | `query` | `migrate`

## 工作流

### Ingest（摄入）

1. 确认来源文件已放入 `raw/<domain>/` 对应目录。
2. PDF/DOCX/PPTX/XLSX 或大量图片资料，先做确定性预处理并建立 manifest。
3. 图片密集资料按 image manifest 分析；必要时调用最多 6 个 default agent 批次做只读图片理解。
4. 阅读/分析来源，并核对 manifest 覆盖率、顺序、缺失和重名问题。
5. 与用户讨论关键要点。
6. 在 `wiki/<domain>/` 创建摘要页面。
7. 用新信息更新相关已有 wiki 页面。
8. 执行强制维护检查：检查/更新 `AGENTS.md`、`CLAUDE.md`、`index.md`、frontmatter、`sources`；若 `index.md` 变化，按 `indexed_page_count` / `wiki_file_count` 数量规则处理 page count；最后追加 `log.md`。

### Query（查询）

1. 读取 `index.md` 了解可用内容。
2. 定位并读取相关 wiki 页面。
3. 综合答案，引用 wiki 页面 `[[标题]]`。
4. 执行强制维护检查；若用户要求只读，则只报告 `AGENTS.md`、`CLAUDE.md`、`index.md` 或 frontmatter 缺口，不自动写入。
5. 如果答案有价值，提议归档为新 wiki 页面。

### Lint（维护）

1. 检查 wiki 页面间矛盾。
2. 找出无入链的孤立页面。
3. 找出值得拥有独立页面的内联提及。
4. 检查缺失的交叉引用。
5. 验证 frontmatter 一致性。
6. 检查 `AGENTS.md`、`CLAUDE.md`、`index.md` 是否需要更新。
7. 按需更新 `index.md`；更新前计算 `indexed_page_count`、`wiki_file_count` 和 footer count，检查未收录文件、断链、重复条目和统计漂移。
8. 追加 lint 报告到 `log.md`，记录 frontmatter 与 index 数量检查结果。

## 限制

- 绝不修改 `raw/` 下的文件。
- 覆盖已有 wiki 内容前须确认。
- `log.md` 条目 append-only，不删除已有条目。
- 不确定时提问，不猜测。
- 保持中文为主要内容语言。
- 不破坏已有 wiki 链接。
- 优化页面时不删除已有图片嵌入。
\```

## 初始化步骤

1. 将上方模板保存到 vault 根目录的 `AGENTS.md`。
2. 如需 Claude Code 兼容，同步保存一份为 `CLAUDE.md`。
3. 替换所有 `<占位符>`。
4. 填写领域注册表。
5. 创建 `raw/<各领域>/` 和 `wiki/<各领域>/`。
6. 创建空的 `index.md` 和 `log.md`。
7. 在 Obsidian 设置中将 attachment folder path 设为 `raw`。
