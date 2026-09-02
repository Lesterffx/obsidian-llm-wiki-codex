# Obsidian LLM Wiki Codex Skill

这是一个面向 Codex 的 Obsidian LLM Wiki Skill，用来让 Codex 持续维护一个结构化的 Obsidian 知识库。

它不是把原始资料简单丢给 RAG 每次重新检索，而是让 LLM 把知识“编译”成一个可持续维护的 wiki：读取 `raw/` 中的原始资料，整理、提炼、交叉引用到 `wiki/`，并维护 `index.md`、`log.md` 和项目 schema。

> 这是 Codex 版。Claude Code 版请见：[Lesterffx/obsidian-llm-wiki](https://github.com/Lesterffx/obsidian-llm-wiki)。

## 灵感来源

本方案灵感来自 Andrej Karpathy 的 [llm-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 知识管理理念。

Karpathy 的核心洞察：大多数人使用 LLM 处理文档的方式是 RAG —— 每次查询时从原始文档中检索片段、重新推导答案。这种方式没有知识积累。问一个需要综合五份文档的复杂问题，LLM 每次都要从头拼凑。

LLM Wiki 的做法不同：LLM **持续构建和维护一个持久化的 wiki** —— 一组结构化、互相链接的 Markdown 文件，位于你和原始资料之间。每当你添加新资料，LLM 不会只为后续检索做索引，而是阅读、提取关键信息、整合到现有 wiki 中 —— 更新实体页面、修正主题摘要、标记新旧数据矛盾、强化或挑战正在形成的综合分析。知识编译一次，然后**保持最新**，而非每次查询重新推导。

这样做的好处是：

- 知识不是每次查询临时重建，而是持续积累。
- 原始资料保持只读，wiki 层负责结构化和提炼。
- 交叉引用、摘要、矛盾、来源和操作记录都可以被持续维护。
- Obsidian 成为人类阅读和浏览知识网络的前端，Codex 成为维护 wiki 的执行者。

Codex 版在这个思路上做了进一步适配：它可以结合项目内 Python 虚拟环境做 PDF/DOCX/PPTX 等文档预处理，也可以通过 image manifest 将大量图片、截图课程和 PPT 页面拆成最多 6 个连续批次；运行时并发不足时按波次执行。主 Codex 负责核对覆盖率、整合结果、写入 wiki、维护索引和安全追加日志。

## 三层架构设计

```text
┌─────────────────────────────────────────┐
│ Schema                                  │
│ AGENTS.md / CLAUDE.md 双入口关系          │
│ 领域注册表、命名约定、工作流、安全规则    │
├─────────────────────────────────────────┤
│ wiki/                                   │
│ LLM 生成和维护的知识层                   │
│ 摘要页面、概念页面、方法论、交叉引用      │
├─────────────────────────────────────────┤
│ raw/                                    │
│ 不可变原始资料层                         │
│ PDF、DOCX、PPTX、网页剪藏、截图、附件     │
└─────────────────────────────────────────┘
```

- `raw/`：不可变原始资料层。Codex 只读取，绝不修改、移动或删除。
- `wiki/`：LLM 维护的知识层。Codex 可以创建、优化、迁移、归档页面，并维护链接和来源。
- `AGENTS.md`：Codex 项目 schema，定义领域、目录、frontmatter、标签、工作流和安全规则。
- `CLAUDE.md`：可选兼容入口。两个文件同时存在时，Skill 会按 vault 声明的关系处理；若声明为完全相同的双入口，则同步修改并校验 SHA-256。
- `index.md`：知识库目录，由 LLM 按 wiki 当前状态维护。
- `log.md`：操作日志，append-only。

## Codex 版功能特点

- **Schema 双入口契约**：读取现有 `AGENTS.md` 与 `CLAUDE.md`；若 vault 声明两者完全相同，则保持字节一致并校验 SHA-256，否则保留有意的运行时差异。
- **强制维护通道**：每次执行都会主动检查 `AGENTS.md`、`CLAUDE.md`、`index.md` 和任务相关 wiki 页 frontmatter；结构缺口默认修复，显式只读时只报告。
- **frontmatter 顶部结构例外**：YAML frontmatter 必须在页面第一行；即使用户要求“补充放最后”或“保留正文顺序”，也会把 frontmatter 作为结构元数据放回顶部。
- **六变量索引健康检查**：更新 `index.md` 前计算 `indexed_page_count`、`wiki_file_count`、`registered_domain_count`，以及 `missing_count`、`broken_count`、`duplicate_count`，并优先使用随 Skill 提供的固定精校脚本统一核对 footer 与索引健康行。
- **frontmatter 与标签规范化**：新增、修改、优化 wiki 页面时检查 YAML frontmatter；tag 中空白会规范为 `_`。
- **schema/index freshness check**：每次执行 Skill 都必须检查 `AGENTS.md`、`CLAUDE.md`、`index.md` 是否需要更新。
- **文档预处理运行时**：优先使用项目 `.venv` 处理 PDF、DOCX、PPTX、XLSX 的文本、页序、slide 顺序、图片 manifest。
- **中文 PDF 固定预处理**：使用随 Skill 提供的脚本提取逐页文本、页码、元数据和嵌入图片，检测替换字符与控制字符；空白页或疑似乱码页自动渲染供视觉核对。
- **任务临时目录闭环**：所有 PDF 中间产物进入独立 `tmp/obsidian-llm-wiki/<task-id>/`，按登记清单逐文件清理，再按最深优先删除空目录；不跨任务、不递归、不批量删除。
- **图片密集资料分析**：先建立 image manifest，再处理截图课程、PPT 截图、raw 图片目录和 wiki 图片引用。
- **最多 6 个总批次读图**：大量图片拆成不超过 6 个连续批次；并发槽不足时分波执行，只读分析后由主 Codex 汇总。
- **低 Token 日志预检**：写入型任务在最终追加日志前调用固定只读 PowerShell 脚本，只返回是否需要轮转的紧凑 JSON，不重复生成检查代码或加载日志正文。
- **大体积日志安全追加与分卷**：`log.md` 使用有限尾部和唯一 EOF 锚点追加；默认在投影大小达到 2 MiB 或跨年时整卷归档，并支持状态、历史查询和显式轮转命令。
- **migrate / delete / remove / de-index 工作流**：支持旧笔记迁移、页面归档、移出索引和谨慎删除。
- **Windows / PowerShell 安全规则**：避免依赖系统 Python，避免批量删除和递归删除。

## 文件结构

```text
obsidian-llm-wiki-codex/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── assets/
│   ├── wiki-page.md
│   ├── book-note.md
│   ├── meeting-note.md
│   ├── tool-page.md
│   └── log-active.md
├── examples/
│   ├── AGENTS.example.md
│   ├── index.example.md
│   ├── log.example.md
│   └── prompt-handbook.example.md
├── references/
│   ├── index_stat.py
│   ├── log-rotation.md
│   ├── pdf-preprocessing.md
│   ├── schema.md
│   └── temp-cleanup.md
├── scripts/
│   ├── log-preflight.ps1
│   └── preprocess_pdf.py
├── requirements-llm-wiki.txt
├── README.md
├── PRIVACY.md
├── LICENSE
└── .gitignore
```

`examples/` 提供可复制到 Obsidian vault 根目录的初始化范例和脱敏实战指令手册；`references/schema.md` 是更完整的通用 schema 参考，`references/index_stat.py` 用于只读精校 `index.md` 六变量，`references/log-rotation.md` 描述日志分卷与恢复规则。

## 安装方式

将本仓库中的 Skill 目录放到你的 Codex skills 目录：

```powershell
%USERPROFILE%\.codex\skills\obsidian-llm-wiki
```

建议目录结构：

```text
%USERPROFILE%\.codex\skills\obsidian-llm-wiki\
├── SKILL.md
├── requirements-llm-wiki.txt
├── agents/
├── assets/
├── references/
└── scripts/
```

安装后重启 Codex，或新开一个 Codex 线程，让 Skill 元数据重新加载。

PDF 预处理额外依赖 `pypdf` 与 `PyMuPDF`。Skill 不会自动安装依赖；确认要启用 PDF 功能后，可由你明确执行以下命令，把固定版本安装到 vault 或项目自己的 `.venv`：

```powershell
& "<vault-root>\.venv\Scripts\python.exe" -m pip install -r "<skill_base>\requirements-llm-wiki.txt"
```

## 快速开始

### 1. 准备 Obsidian Vault

推荐结构：

```text
<你的 vault>/
├── AGENTS.md
├── index.md
├── log.md
├── raw/
│   └── <领域>/
└── wiki/
    └── <领域>/
```

如果你已经有 Claude Code 版 `CLAUDE.md`，可以继续兼容使用；若同时维护 `AGENTS.md`，请在 vault schema 中声明两者是字节一致的双入口，还是允许保留运行时差异。

### 2. 初始化 schema

第一次使用时，可以直接复制初始化范例到你的 Obsidian vault 根目录：

```text
examples/AGENTS.example.md  →  AGENTS.md
examples/index.example.md   →  index.md
examples/log.example.md     →  log.md
```

完成初始化后，可参考 [Codex 版实战指令手册](examples/prompt-handbook.example.md) 编写 ingest、优化、图片批量分析、文档预处理、迁移和归档等任务指令。手册中的目录和页面名称与上述初始化范例保持对应，使用时替换为你自己的 vault 路径即可。

然后按自己的知识库修改 `AGENTS.md` 中的领域注册表、raw/wiki 路径和标签体系。

`references/schema.md` 提供更完整的通用 schema 模板，可作为进阶参考。项目级 `AGENTS.md` 应该描述：

- raw/wiki 目录结构
- 领域注册表
- frontmatter 规范
- 标签体系
- wiki 链接规则
- 图片管理规则
- 变更联动规则
- 日志预检、追加和分卷规则
- ingest/query/lint/migrate/index 工作流

### 3. 放入原始资料

把 PDF、DOCX、PPTX、网页剪藏、截图、课程图片等放入 `raw/<领域>/`。

`raw/` 是事实来源和附件层，默认只读。

### 4. 调用 Skill

示例：

```text
$obsidian-llm-wiki ingest @raw/领域/示例资料目录/
```

```text
$obsidian-llm-wiki query “这个知识库里关于某个主题的核心方法论是什么？”
```

```text
$obsidian-llm-wiki 优化 @wiki/AI/某页面.md，保留现有图片和顺序，只追加总结内容到 ## 相关 前。
```

## 常用指令示例

### Ingest 新资料

```text
$obsidian-llm-wiki ingest @raw/领域/资料目录/
```

适合新 PDF、DOCX、PPTX、截图课程、图片目录进入 `raw/` 后处理。

### 图片密集资料

```text
$obsidian-llm-wiki 优化 @wiki/路径/页面.md，图片很多。请先建立 image manifest，保持图片顺序，拆成不超过 6 个总批次；并发不足时按波次调用 default agents 只读分析。
```

### 保留正文并追加总结

```text
$obsidian-llm-wiki 优化 @wiki/领域/示例页面.md，不修改现有正文和图片顺序；补充资料总结、洞见、方法论提炼、最佳实践和金句精选，放在最后面。
```

这类任务会保留正文和图片顺序；如果页面缺少 YAML frontmatter，Skill 仍会把 frontmatter 作为结构维护例外补到页面顶部。

### 刷新索引

```text
$obsidian-llm-wiki 刷新 index.md，检查是否有新增、删除、迁移或重命名的 wiki 页面，并校验底部统计。
```

刷新索引时会先扫描 `wiki/**/*.md`，同时读取 `index.md` 现有条目，分别计算三项权威变量：`indexed_page_count`、`wiki_file_count`、`registered_domain_count`；再计算三项健康变量：`missing_count`、`broken_count`、`duplicate_count`。`.canvas`、示例占位和 `raw/...` 来源链接不计入 Wiki Markdown 页面数。

Skill 自带固定的六变量精校脚本，使用项目允许的 Python 运行时执行；普通模式适合人工核对，`--json` 适合机器读取：

```powershell
& ".\.venv\Scripts\python.exe" "<skill_base>\references\index_stat.py" "<vault_root>"
& ".\.venv\Scripts\python.exe" "<skill_base>\references\index_stat.py" "<vault_root>" --json
```

脚本只读扫描 vault，不硬编码任何知识库路径、领域或统计数字；Codex 环境优先从 `AGENTS.md` 读取领域注册表，并在存在 `CLAUDE.md` 时对照两份 schema。

footer 同时展示已索引页面数、实际 Wiki 文件数和注册领域数，下一行展示未收录、Markdown 断链和重复条目。若已有 `wiki/示例页面.md` 第一次补录进 `index.md`，按 `补录既有页面 / first-time index backfill` 处理；旧 footer 失真时重新计算全部六项变量并记录 `统计漂移修正`，不得在旧数字上盲目递增。

```markdown
_统计：{indexed_page_count} 个已索引页面 | {wiki_file_count} 个 Wiki 文件 | {registered_domain_count} 个注册领域 | 上次更新于 YYYY-MM-DD_

> 索引健康：未收录 {missing_count} | Markdown 断链 {broken_count} | 重复条目 {duplicate_count}；`.canvas`、示例占位和 `raw/...` 链接不计入页面数。
```

### 日志状态、查询与分卷

查看活动日志状态，不修改文件：

```text
$obsidian-llm-wiki log status
```

按日期、操作或关键词查询活动日志和历史分卷：

```text
$obsidian-llm-wiki log query "YYYY-MM-DD optimize"
```

显式轮转模式：

```text
$obsidian-llm-wiki log rotate now
$obsidian-llm-wiki log rotate year
$obsidian-llm-wiki log rotate size
$obsidian-llm-wiki log rotate auto
```

`ingest`、`optimize`、`migrate`、`index`、删除/归档/重命名和修复型 lint/audit 等写入任务，在追加最终日志前运行固定的 `scripts/log-preflight.ps1`。预检按“当前 `log.md` 字节数 + 实际待追加文本的 UTF-8 字节数”计算投影大小；默认达到 2 MiB 或活动卷跨年时才进入完整轮转。query、只读 audit、`log status`、`log query` 和没有文件变化的任务不会自动轮转。

轮转采用整文件移动，不拆分或重写历史内容。活动日志保留在 `log.md`，历史卷存放在 `logs/archive/`，分卷清单为 `logs/log-archives.md`。新活动日志从 `assets/log-active.md` 创建，不复制旧条目；`logs/` 位于 `wiki/` 之外，不计入索引统计。

> 分卷只是整理日志，不等同于独立备份。历史卷不得自动删除、压缩、合并或继续追加；真正的备份应存放在单独管理的位置。

### PDF / DOCX / PPTX

```text
$obsidian-llm-wiki ingest @raw/<领域>/示例资料.pdf，先做 PDF 预处理，提取中文文本、页码、元数据和图片 manifest；疑似乱码或空白页面再做视觉读取，完成 wiki 后清理本次任务临时目录。
```

PDF 使用固定入口，不为每个任务临时生成解析脚本：

```powershell
& ".\.venv\Scripts\python.exe" "<skill_base>\scripts\preprocess_pdf.py" `
  --input "<vault-root>\raw\<领域>\示例资料.pdf" `
  --vault-root "<vault-root>" `
  --task-id "YYYYMMDD-example-ingest"
```

输出固定写入 `<vault-root>/tmp/obsidian-llm-wiki/<task-id>/`，包括：

- `metadata.json`：源文件哈希、PDF 元数据和页数；
- `pages.json`、`page_text.md`：逐页文本、选择的提取器、乱码指标和视觉读取状态；
- `image_manifest.csv`、`unique_image_manifest.csv`、`images/`：图片出现位置与去重图片；
- `rendered_pages/`：仅包含文本为空或疑似乱码的页面；
- `created_files.json`：本次创建的文件、目录和安全清理边界。

中文文本优先由 `pypdf` 提取；只有它不合格且 PyMuPDF 结果更好时才逐页降级。两种文本都为空或疑似乱码时，正文只保留“需视觉读取”占位，不把乱码写入 wiki。

清理与 PDF 读取是两个独立工作流。完成 wiki、索引和验证后，先依据 `created_files.json` 逐个删除登记文件，再按 `created_directories` 从最深层删除已确认的空目录。始终保留 `tmp/`，不处理其他任务或其他工作流目录；若执行策略阻止空目录删除，保留空目录并如实报告，不能换用递归或批量命令绕过。

### 只读评估

```text
$obsidian-llm-wiki 只读评估 @raw/路径/，不修改任何文件，只统计资料规模并给出处理策略。
```

### 迁移旧笔记

```text
$obsidian-llm-wiki migrate @旧笔记路径/ 到 wiki/目标领域/，先评估迁移清单和冲突，再执行。
```

### 移出索引或归档

```text
$obsidian-llm-wiki 将 @wiki/路径/页面.md 从 index.md 中移出，但不要删除文件。
```

## 与 Claude Code 版的区别

| 项目 | Claude Code 版 | Codex 版 |
|---|---|---|
| 仓库 | `Lesterffx/obsidian-llm-wiki` | `Lesterffx/obsidian-llm-wiki-codex` |
| 主要 schema | `CLAUDE.md` | 读取 `AGENTS.md` / `CLAUDE.md`，按 vault 声明处理双入口关系 |
| Agent 能力 | Claude Code 工作流 | Codex 主 agent + default agents 批量图片分析 |
| 文档预处理 | 以 Claude 工作流为主 | 支持项目 `.venv` 做确定性预处理 |
| 图片处理 | 保留图片引用，按需分析 | image manifest + 最多 6 个总批次，必要时分波执行 |
| 适用环境 | Claude Code | Codex / Codex App |

## 隐私与安全

不要把以下内容上传到公开仓库：

- 你的 Obsidian vault。
- `raw/` 原始资料、截图、课程文件、扫描件。
- `wiki/` 中包含个人、客户、课程或商业隐私的页面。
- 项目级 `AGENTS.md`、`CLAUDE.md`、`index.md`、`log.md`。
- 私人 vault 生成的 `logs/`、`logs/archive/` 和 `logs/log-archives.md`。
- 私人 vault 生成的 `tmp/`、PDF 提取文本、页面渲染、图片、JSON/CSV manifest 和 `created_files.json`。
- `.venv/`、缓存、临时文件。
- API key、token、cookie、密钥、账号信息。
- 本机绝对路径和个人目录结构。

本仓库只发布通用 Skill 和模板，不包含任何个人知识库资料。

公开示例应使用 `<你的 vault>`、`raw/<领域>/`、`wiki/<领域>/`、`示例页面.md` 这类占位符或虚构名称；不要把真实课程名、客户名、内部项目名、本机路径或私人页面名写入仓库。

更多检查清单见 `PRIVACY.md`。

## License

MIT License. See `LICENSE`.
