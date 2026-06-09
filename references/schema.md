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

每个 wiki 页面必须以 YAML frontmatter 开头：

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

新增、修改或优化任何 wiki 页面前，必须先检查 YAML frontmatter 是否存在。若不存在，必须在正文前补齐上述笔记属性；若字段缺失，必须修复缺失字段，并在内容或标签发生变化时更新 `updated`。

## 标签体系

| 类别 | 模式 | 示例 |
|---|---|---|
| 类型 | `type/<类别>` | `type/book`, `type/会议`, `type/工具` |
| <自定义> | `<前缀>/<主题>` | `AI/编程`, `工具/编程工具/Codex` |

Frontmatter 的 `tags` 字段是权威来源。如果存在 inline tags，应与 frontmatter 匹配。

### 标签规范化

- 标签只在 frontmatter `tags` 与 inline `#tag` 中规范化，不自动改 `domain`、`sources`、raw/wiki 路径、目录名、文件名、页面标题、wiki 链接、图片嵌入或正文普通文本。
- 标签片段中如有空白，统一用 `_` 连接。例如：`AI Live` → `AI_Live`，`一堂/AI Live` → `一堂/AI_Live`。
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

1. YAML frontmatter
2. Inline tags（兼容 tag-wrangler 插件）
3. 一句话摘要（以 `>` 引用格式）
4. 正文内容
5. `## 相关` — wiki 链接到相关页面
6. `## 来源` — 引用 raw 来源

## 变更联动

任何一次 LLM Wiki 操作（ingest、query、lint、migrate、index、delete/remove、optimize、提炼思维等）都必须考虑 `AGENTS.md`、`CLAUDE.md`、`index.md` 是否保持最新。可以检查后不修改，但必须纳入判断；若本次操作产生任何文件变更，必须在 `log.md` 记录三者检查结果。

每次创建或修改 wiki 页面后，必须级联执行以下操作：

| 操作 | 触发条件 | 说明 |
|---|---|---|
| 检查/更新 `AGENTS.md` | 任何 LLM Wiki 操作 | 检查领域注册表、raw/wiki 路径、处理规则、安全规则、标签规则是否需要更新 |
| 检查/更新 `CLAUDE.md` | 任何 LLM Wiki 操作 | 检查是否需要与 `AGENTS.md` 的共享 schema 保持兼容同步 |
| 检查/更新 `index.md` | 任何 LLM Wiki 操作；页面新增、删除、迁移、标签或摘要变化时通常需要更新 | 注册新页面、更新摘要、调整页面计数、移除或修正旧条目 |
| 追加 `log.md` | 任何 wiki 变更 | 记录操作类型、变更内容、影响范围 |
| 更新 `sources` | 新建页面 / 发现来源为空 | 指向对应的 raw 目录或文件 |
| 更新相关 wiki 页面 | 新内容影响已有页面 | 交叉引用、修正矛盾、补充新信息 |

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
8. 按变更联动规则检查/更新 `AGENTS.md`、`CLAUDE.md`、`index.md`、`sources`，并追加 `log.md`。

### Query（查询）

1. 读取 `index.md` 了解可用内容。
2. 定位并读取相关 wiki 页面。
3. 综合答案，引用 wiki 页面 `[[标题]]`。
4. 考虑 `AGENTS.md`、`CLAUDE.md`、`index.md` 是否存在过期风险；只读查询默认报告建议，不自动修改。
5. 如果答案有价值，提议归档为新 wiki 页面。

### Lint（维护）

1. 检查 wiki 页面间矛盾。
2. 找出无入链的孤立页面。
3. 找出值得拥有独立页面的内联提及。
4. 检查缺失的交叉引用。
5. 验证 frontmatter 一致性。
6. 检查 `AGENTS.md`、`CLAUDE.md`、`index.md` 是否需要更新。
7. 按需更新 `index.md`。
8. 追加 lint 报告到 `log.md`。

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
