# AGENTS.md / CLAUDE.md 通用模式模板

> 新 Obsidian vault 使用 `AGENTS.md` 作为 Codex schema；如需兼容 Claude Code，可同时保留 `CLAUDE.md`。请在 schema 中声明两者是字节一致的双入口，还是允许保留运行时差异；声明为一致时，每次结构修改都必须同步并校验 SHA-256。

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
- **AGENTS.md** — Codex 项目 schema 入口。
- **CLAUDE.md** — 可选兼容入口；与 `AGENTS.md` 的关系由本 schema 声明。
- **index.md** — 内容目录（LLM 维护）。
- **log.md** — 操作日志（append-only）。

## Schema 入口关系

- `AGENTS.md` 与 `CLAUDE.md`：`<字节一致 | 保留运行时差异>`。
- 选择“字节一致”时，修改任一文件必须同步修改另一文件，并在写入后校验 SHA-256 相同。
- 选择“保留运行时差异”时，共享 schema 规则必须兼容；发生冲突时 Codex 遵循 `AGENTS.md`，并报告与任务相关的冲突。

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
- 图片少量时由主 Codex 直接分析；图片较多时可调用内置 `default` agents 分批分析。
- `default` agents 只读图片并返回分析结果，不修改 `raw/`、`wiki/`、`index.md`、`log.md` 或 schema 文件。
- 1–10 张由主 Codex 分析；11–30 张拆成 2–3 批；31 张以上拆成不超过 6 个总批次。并发槽不足时按波次执行，不再增加批次数。

### 文档预处理运行时

- 如果项目存在 `.venv`，优先使用项目内 Python：

\```powershell
& ".\.venv\Scripts\python.exe" ".\scripts\<script>.py" "<input-path>" "<output-path>"
\```

- PDF/DOCX/PPTX/XLSX 等文档先用 `.venv` 做确定性预处理：提取文本、元数据、内嵌图片、页序、slide/page 顺序和 manifest。
- `.venv` 负责可重复的解析、排序、抽取和 manifest；`default` agents 负责 OCR-like 图片阅读、截图理解、图表理解和洞见提炼。
- 不默认假设 Tesseract、OpenCV、PaddleOCR、RapidOCR 等传统 OCR 引擎可用。

PDF 使用 Skill 固定脚本，不为每个任务生成临时解析脚本：

\```powershell
& ".\.venv\Scripts\python.exe" "<skill_base>\scripts\preprocess_pdf.py" `
  --input "<PDF绝对路径>" `
  --vault-root "<vault绝对路径>" `
  --task-id "<时间戳-安全任务标识>"
\```

- 依赖固定在 `requirements-llm-wiki.txt`，不得自动安装；缺少依赖时报告并由用户决定是否安装到项目 `.venv`。
- PDF 文本、图片、渲染页和 manifest 只能写入 `tmp/obsidian-llm-wiki/<task-id>/`，不得写入 `raw/`。
- PDF 读取和临时文件清理是两个独立工作流；页面、索引和验证完成后再进入清理。
- 清理权限来自本次 `created_files.json`。文件逐个删除；空目录按 `created_directories` 最深优先逐个删除；`tmp/obsidian-llm-wiki/` 仅在完全为空时删除，始终保留 `tmp/`。
- 禁止递归、通配符、管道、循环、数组和批量删除；执行策略阻断空目录删除时保留空目录并报告，不得改用等价命令绕过。

## 页面结构

必需结构：YAML frontmatter 位于文件第一行；存在 inline tags 时与 frontmatter 一致；标签片段中的空格规范为 `_`。

按资料类型和任务范围选用一句话摘要、正文、`## 相关` 与 `## 来源`。不要为了套模板而扩写只读查询或轻量维护任务。

## 变更联动

任何一次 LLM Wiki 操作（ingest、query、lint、migrate、index、delete/remove、optimize、提炼思维等）都必须执行强制维护检查：主动检查 `AGENTS.md`、`CLAUDE.md`、`index.md` 和任务相关 wiki 页 frontmatter 是否保持最新。可以检查后不修改，但必须纳入判断；若发现结构缺口，默认修复。显式只读/审计/no-write 请求优先，此时只报告缺口。

每次创建或修改 wiki 页面后，必须级联执行以下操作：

| 操作 | 触发条件 | 说明 |
|---|---|---|
| 检查/更新 `AGENTS.md` | 任何 LLM Wiki 操作 | 检查领域注册表、raw/wiki 路径、处理规则、安全规则、标签规则是否需要更新 |
| 检查/更新 `CLAUDE.md` | 任何 LLM Wiki 操作 | 按 vault 声明保持字节一致，或保留有意的运行时差异 |
| 检查/更新 `index.md` | 任何 LLM Wiki 操作；页面新增、删除、迁移、标签或摘要变化时通常需要更新 | 注册、补录或修正条目；修改前计算三项权威变量和三项健康变量 |
| 追加 `log.md` | 任何 wiki 变更 | 记录操作类型、变更内容、影响范围 |
| 更新 `sources` | 新建页面 / 发现来源为空 | 指向对应的 raw 目录或文件 |
| 更新相关 wiki 页面 | 新内容影响已有页面 | 交叉引用、修正矛盾、补充新信息 |

### index.md 数量规则

- 修改 `index.md` 前计算三项权威变量：`indexed_page_count`、`wiki_file_count`、`registered_domain_count`。
- 同次扫描计算三项健康变量：`missing_count`、`broken_count`、`duplicate_count`。
- footer 使用：`_统计：{indexed_page_count} 个已索引页面 | {wiki_file_count} 个 Wiki 文件 | {registered_domain_count} 个注册领域 | 上次更新于 YYYY-MM-DD_`。
- 健康行使用：`> 索引健康：未收录 {missing_count} | Markdown 断链 {broken_count} | 重复条目 {duplicate_count}；.canvas、示例占位和 raw/... 链接不计入页面数。`
- 既有文件首次收录按 `补录既有页面` 处理；旧统计失真时重新计算全部六项变量并记录 `统计漂移修正`，不得盲目递增。
- 修改后确认 footer 和健康行各出现一次；`.canvas`、图片、附件、外链、schema、示例占位与 `raw/...` 来源不计入 Wiki Markdown 页面数。

### log.md 格式

\```markdown
## [YYYY-MM-DD] <action> | <title>

- 范围：本次任务及边界。
- 变更：涉及的文件和操作。
- 资料：来源、图片或附件核对结果。
- 维护：frontmatter=<valid/repaired/n-a>；index=<unchanged/refreshed>；schema=<unchanged/updated, hash-equal>；raw=unchanged。
- 验证：实际执行的检查及结果。
- 未决：存在异常时填写。
\```

`范围`、`变更`、`维护`、`验证`为必需字段；`资料`和`未决`按需填写。`index.md` 变化时在`维护`中记录三项权威变量和三项健康变量。不得改写历史条目以适配新格式。

写入型任务在最终追加前调用 Skill 的 `scripts/log-preflight.ps1`，按当前日志字节数加实际待追加UTF-8字节数计算投影大小；默认达到2 MiB或活动日志跨年时轮转。query、只读 lint/audit、`log status`、`log query`和没有文件变化的任务不自动轮转。

支持 `log status`、`log query`、`log rotate now`、`log rotate year`、`log rotate size`、`log rotate auto`。普通追加只在 PowerShell 内部读取末尾80行，必要时最多200行，只返回重复标题判断和唯一EOF锚点；使用 `apply_patch` 一次追加，并验证旧内容前缀哈希不变。

轮转时把完整旧 `log.md` 原样移动到 `logs/archive/log-YYYY-MM-DD-to-YYYY-MM-DD.md`，用 `assets/log-active.md` 创建新日志，并在 `logs/log-archives.md` 记录分卷。不得复制后清空、拆分、改写、覆盖或继续追加历史卷；`logs/` 不计入Wiki页面统计，分卷不等于独立备份。

操作类型：`ingest` | `optimize` | `lint` | `audit` | `query` | `migrate` | `index` | `rotate`

## 工作流

### 延后同步与队列合并

enhance-wiki-content、optimize、update-raw-reference、ingest、delete 可在命令名后带 `--defer`。页面级工作和验证照常，index 编辑、六变量精校、顶部维护/统计/健康行同步、日志追加延后；在 logs/queue 写专属 queue v1 片段即完成本任务。无变化且无待补录事项不入队。

`sync` 无位置参数，是批次共享文件唯一写者：全流程先持锁，固定快照，兑现明确索引动作，精校、预检并准确追加片段日志及一条最终记录，验证后逐个单文件清理，最后释放锁。`sync --dry-run` 零写入；空队列已一致不修改文件。完整 SOP 见 Skill 的 references/defer-sync.md。

logs/queue 非 Wiki，不计入统计；真实片段产生目录不等于预建空 logs/archive。统计滞后以最近一次 sync 为准，query/lint 不代补已有队列片段页面。同页不能并行；跨运行时完整保证需要使用同一锁 SOP，旧实现不保证行为等价。

### Ingest（摄入）

1. 确认来源文件已放入 `raw/<domain>/` 对应目录。
2. PDF/DOCX/PPTX/XLSX 或大量图片资料，先做确定性预处理并建立 manifest。
3. 图片密集资料按 image manifest 分析；必要时拆成不超过 6 个总批次，并按可用并发槽分波调用 default agents 做只读图片理解。
4. 阅读/分析来源，并核对 manifest 覆盖率、顺序、缺失和重名问题。
5. 与用户讨论关键要点。
6. 在 `wiki/<domain>/` 创建摘要页面。
7. 用新信息更新相关已有 wiki 页面。
8. 执行强制维护检查：检查/更新 `AGENTS.md`、`CLAUDE.md`、`index.md`、frontmatter、`sources`；若 `index.md` 变化，重新计算三项权威变量和三项健康变量；最后安全追加 `log.md`。

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
7. 按需更新 `index.md`；更新前计算三项权威变量和三项健康变量，检查未收录文件、断链、重复条目和统计漂移。
8. 追加 lint 报告到 `log.md`，记录 frontmatter 与 index 数量检查结果。

## 限制

- 绝不修改 `raw/` 下的文件。
- 覆盖已有 wiki 内容前须确认。
- `log.md` 条目 append-only，不删除已有条目。
- 大日志只做定量 tail 读取与安全补丁追加，不整文件读取或重写。
- 不确定时提问，不猜测。
- 保持中文为主要内容语言。
- 不破坏已有 wiki 链接。
- 优化页面时不删除已有图片嵌入。
- 普通目录禁止删除；唯一例外是本次 `tmp/obsidian-llm-wiki/<task-id>/` 中已登记且确认为空的目录，以及完全为空的 `tmp/obsidian-llm-wiki/` 工作容器。每次只能删除一个明确目录，且不得使用 `-Recurse`。
\```

## 初始化步骤

1. 将上方模板保存到 vault 根目录的 `AGENTS.md`。
2. 如需 Claude Code 兼容，可保存一份为 `CLAUDE.md`，并明确声明它与 `AGENTS.md` 是字节一致还是保留运行时差异。
3. 替换所有 `<占位符>`。
4. 填写领域注册表。
5. 创建 `raw/<各领域>/` 和 `wiki/<各领域>/`。
6. 创建空的 `index.md` 和 `log.md`。
7. 在 Obsidian 设置中将 attachment folder path 设为 `raw`。
