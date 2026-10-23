# Obsidian LLM Wiki Codex Skill

这是一个面向 Codex 的 Obsidian LLM Wiki Skill，用来让 Codex 持续维护一个结构化的 Obsidian 知识库。

以本地开发与使用版本为准，本仓库用于脱敏备份。备份 PR 保留供审阅，不自动合并，也不反向覆盖本地安装；仓库内容不包括私人知识库和运行资料。

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

- **延后同步与队列合并**：五种页面写命令支持 `--defer`，页面完成后写专属片段；批次末尾 `sync` 统一维护索引、统计和日志，`sync --dry-run` 零写入。详见 [defer/sync SOP](references/defer-sync.md)。

### 批量任务：defer → sync

```text
$obsidian-llm-wiki enhance-wiki-content --defer "wiki/<领域>/<页面>.md" ["raw/<领域>/<资料>/"]
$obsidian-llm-wiki optimize --defer "wiki/<领域>/<页面>.md"
$obsidian-llm-wiki update-raw-reference --defer "wiki/<领域>/<页面>.md" "raw/<领域>/<资料>/"
$obsidian-llm-wiki ingest --defer "raw/<领域>/<来源>"
$obsidian-llm-wiki delete --defer "wiki/<领域>/<页面>.md"
$obsidian-llm-wiki sync --dry-run
$obsidian-llm-wiki sync
```

参数紧跟命令名，不改变原有页面保护规则。片段位于私人 vault 的 logs/queue，内含现成索引行和日志；统计滞后至 sync 属于正常状态。不同页可并行，同页必须串行；未带参数的默认流程不变。空队列已一致时零写入，缺失/冲突片段保留报告。

两端均可发起合并，普通片段兼容 ZCode queue v1。要使用完整锁与恢复校验，两端调用新增的同一 helper/SOP，无需修改 ZCode 目录。直接调用旧 ZCode sync 仍有锁仅覆盖日志、删除片段受限、标题去重等差异，不保证双向行为等价，也不得与新版同时运行。

新增 `references/defer-sync.md`、`assets/queue-fragment.md`、`scripts/flush_queue.py`。helper 从不自动删除；agent 逐文件验证并清理。真实 queue、锁、payload、日志、测试产物不得上传，公开测试仅用虚构内容。

### 其他功能

- **文末增强**：`enhance-wiki-content` 保留正文和媒体，在末尾补充六类内容；指定 raw 目录时读取范围内图片与视频，`--no-video` 可关闭视频读取，仅给页面时只基于正文。补齐缺失标准字段，并对缺失、空或去重后零/一个有效标签的 tags 追加有依据的类型、领域和主题标签；保留旧标签，仅新增标签时更新 `updated` 并同步唯一既有索引的标签列。独立 inline 标签区只追加新标签，其他元数据与正文保持。详见[稀疏标签匿名验收](references/sparse-tag-validation.md)。
- **媒体引用修复与旧节清理**：`update-raw-reference` 保留既有 Obsidian `![[...]]` 媒体及 Markdown 图片修复规则，新增 raw PDF 附件链接全路径嵌入化，并清理精确名为「总结／洞察」且无保护引用的旧节；不新增任何内容节，不改动 raw 文件。
- **图片搭配文字查询**：`query-image` 先验证视觉能力，再结合截图、图表或扫描件与可选问题检索 Wiki；默认只读，维护缺口只报告，多图自动按连续批次分析。
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
│   ├── directory-batch.md
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

### Query Image 图片搭配文字查询

这是 Skill 工作流入口，无需安装额外命令行程序。单图加问题：

```text
$obsidian-llm-wiki query-image "<图片目录>/试题截图.png" "这道题涉及哪些库内知识？"
```

多图加问题，按输入顺序分析：

```text
$obsidian-llm-wiki query-image "<图片目录>/图表一.png" "<图片目录>/图表二.png" "比较两张图，并引用相关 Wiki。"
```

也可以附上当前对话图片后输入 `$obsidian-llm-wiki query-image`。不提供问题时，默认查找图片涉及的库内知识并解释关联。缺失或无法唯一定位的图片会被明确标记，不会自动扫描相邻目录。

- **视觉前提**：先用一张输入图片验证原生视觉能力；不可用时才尝试已配置且获准使用的视觉 MCP。文件名、URL 回执和元数据不算读图成功。所有允许的视觉通道均不可用时终止图片查询，提示改用文字 `query`。
- **自动并行**：1–10 张由主线程读取；11–30 张拆成 2–3 个连续批次；31 张以上拆成 6 个规模接近的连续批次。该命令明确允许只读 default agents，实际并发服从可用槽位与更高优先级规则；槽位不足时分波，禁止或无法委派时由主线程处理原批次。
- **轻量提取与引用**：逐图提取可见文字、代码片段、实体、检索词和存疑区域，按输入清单对账。答案区分“图片识别内容／库内事实／推论”，引用已确认存在的 `[[页面标题]]`，无匹配时如实说明。
- **默认只读**：此命令是通用自动维护规则的例外。即使发现 frontmatter、schema 或 index 缺口，也只报告，不修改任何知识库文件，不写日志、不分卷、不保存 manifest、不自动复制输入图片。
- **归档需明确授权**：默认仅建议归档；获准后走独立写入流程，创建纯文字页面，来源说明标注“查询输入截图”。没有已验证的 raw 来源时使用 `sources: []`；需要图片入库时另行明确要求，并遵守目标知识库的来源规则，不覆盖或修改既有 raw 资料。

### 图片密集资料

```text
$obsidian-llm-wiki 优化 @wiki/路径/页面.md，图片很多。请先建立 image manifest，保持图片顺序，拆成不超过 6 个总批次；并发不足时按波次调用 default agents 只读分析。
```

### 保留正文并追加总结

需要固定的六类文末增强，可使用以下两种入口。这是 Skill 工作流，无需安装额外命令行程序。

指定图片来源，基于原正文与图片提炼：

```text
$obsidian-llm-wiki enhance-wiki-content "wiki/<领域>/<页面>.md" "raw/<领域>/<资料名>/"
```

只基于原正文提炼：

```text
$obsidian-llm-wiki enhance-wiki-content "wiki/<领域>/<页面>.md"
```

两种方式均按顺序在原正文末尾追加 **资料总结、洞见、方法论提炼、最佳实践、金句精选、关联 Wiki**。第一参数必须是当前 vault 的 `wiki/` 内既有 Markdown 文件或目录；可选来源必须是 `raw/` 内既有目录。文件输入沿用单页行为，目录输入按下节规则展开。参数数量、类型或路径错误（含符号链接越界）时零写入，不创建目标页面或来源目录。

- **原文保留**：除独立 inline 标签区可按稀疏标签例外追加新标签外，原正文、链接、图片、视频与音频嵌入、显示参数及顺序均保持不变，不修复媒体路径，不插入新媒体。其余新增正文仅追加到原 EOF，保留原换行符；补丁工具无法保留 CRLF 等格式或日志历史前缀时，停止写入并报告，不转换格式来继续操作。
- **两种资料范围**：指定 raw 目录时先建有序 media manifest，对账嵌入、视频附件链接及范围内未引用媒体；图片按既有批次规则读取，视频默认按[视频读取规则](references/video-reading.md)处理，`--no-video` 跳过视频探测、读取及附属字幕查找。缺失、重名、越界或无法识别均报告，不猜测。只给页面时始终不读媒体、不读取 raw 正文，也不因 `sources` 存在而扩大来源。两种方式均不进行语音转写。
- **缺失与稀疏标签才补**：缺整块 frontmatter 或标准字段时补齐七字段；原始 tags 缺失、为空或去重后零/一个有效标签时，保留旧标签并依据 Schema 与本页证据补充多个标签，只在新增标签时更新 `updated`。已有两个及以上有效标签不变；其他字段逐字保留，不安全 YAML 或标签结构导致整项零写入。已有索引仅允许同步本次补齐后的标签列，保留链接、摘要和分区；未收录页仍只向合适的既有分区补录。索引变化时刷新维护说明并重算六变量，校验 `footer_match=true`。歧义、Schema 和无关问题只报告。
- **有据提炼**：区分资料事实与推论；金句标明原文摘录或“提炼表达（非原文引用）”；关联 Wiki 必须存在且能唯一解析，材料不足时明确说明。重复执行先比对已有内容，六类内容已覆盖则不机械重复追加，部分缺失则仅补不足。
- **变更验证**：实际修改后才预检并追加一次日志；记录标签触发条件、原标签、新增标签与日期处理。除标签容器、独立 inline 区插入和条件性 `updated` 变化外，其他元数据及原正文保持，媒体/raw/日志历史前缀不变。重复执行不重复追加标签；无变化不改日期、不写日志。

需要自定义章节或插入位置时，继续使用一般优化指令：

```text
$obsidian-llm-wiki 优化 @wiki/领域/示例页面.md，不修改现有正文和图片顺序；补充资料总结、洞见、方法论提炼、最佳实践和金句精选，放在最后面。
```

一般优化遵循默认维护规则；`enhance-wiki-content` 仅允许缺失字段修复和上述稀疏标签、日期及索引标签同步例外。defer 通过现有 queue v1 片段记录 `tag-sync`，由 sync 更新标签列，不改变其他命令权限。

### Wiki 目录批量处理与注意事项

`enhance-wiki-content` 和 `update-raw-reference` 的第一参数为目录时，只处理其直属 `.md`，不递归进入子目录；按自然文件名顺序逐页执行，例如 `2` 排在 `10` 前。第二参数是 raw 根目录，每页只匹配其下与 Markdown 文件名去掉 `.md` 后完整同名的直属子目录，不按编号、模糊名称或列表位置配对。

```text
$obsidian-llm-wiki enhance-wiki-content "wiki/<领域>/<章节>/" "raw/<领域>/<章节>/"
$obsidian-llm-wiki enhance-wiki-content --no-video --defer "wiki/<领域>/<章节>/" "raw/<领域>/<章节>/"
$obsidian-llm-wiki enhance-wiki-content "wiki/<领域>/<章节>/"
$obsidian-llm-wiki update-raw-reference --defer "wiki/<领域>/<章节>/" "raw/<领域>/<章节>/"
```

| 情形 | 文末增强 | 媒体引用修复 |
|---|---|---|
| 有完整同名 raw 子目录 | 沿用双参数单页规则 | 在该子目录内匹配媒体 |
| 缺少同名 raw 子目录 | 降为单参数，仅用本页正文 | 整页跳过，不改引用、元数据、索引、日志或队列 |
| 不提供 raw 参数 | 全部直属页面仅用本页正文 | 参数缺失，零写入 |

不能使用 raw 根目录、编号相同的其他目录或其他页的来源代替。文件输入保持兼容：显式 raw 目录可与页面不同名，不追加页面名。

执行前固定逐页清单，检查参数、真实路径及全部待执行页的 frontmatter；安全错误整批零写入，空目录无操作。标志沿用原适用范围，引用修复不接受 `--no-video`；不自动启用 defer、sync、子 agent 或并行。普通模式逐变化页收尾，defer 逐页入队；跳过/无变化页不生成日志或片段。最终逐页报告有效来源、模式、变化、跳过和失败，部分失败不算整批成功。

详见[共用目录规则和虚构验收案例](references/directory-batch.md)。真实展开清单、匹配结果和跳过原因也属于私人资料，不复制到公开 commit 或 PR。

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

### Update Raw Reference 修复媒体引用与清理旧节

来源目录迁移后，指定一个既有 Wiki 页面及 raw 目录，执行媒体引用修复、raw PDF 附件链接嵌入化及旧「总结／洞察」节清理：

```text
$obsidian-llm-wiki update-raw-reference "wiki/<领域>/<页面>.md" "raw/<领域>/<资料名>/"
```

两参数必填，必须是当前 vault 中真实存在且分别位于 `wiki/`、`raw/` 内的目标：第一参数为 Markdown 文件或目录，第二参数为目录；顶层路径越界、类型错误或缺失时零写入。单文件模式中页面与资料目录不同名不影响执行；目录模式只匹配完整同名的直属 raw 子目录，缺失则整页跳过，详见[目录规则](references/directory-batch.md)。

所有匹配成功的图片、视频及音频均使用从 `raw/` 开始的完整目录路径，不只针对易重名文件，也不使用本机盘符绝对路径。例如，指定目录 `raw/领域/资料名称/`：

```text
![[image-001.png|800]]
→ ![[raw/领域/资料名称/image-001.png|800]]

![[video-001.mp4]]
→ ![[raw/领域/资料名称/video-001.mp4]]

![[audio-001.mp3]]
→ ![[raw/领域/资料名称/audio-001.mp3]]

![image-001.png](旧附件/image-001.png)
→ ![[raw/领域/资料名称/image-001.png]]

![示例 图.png](旧附件/示例%20图.png)
→ ![[raw/领域/资料名称/示例 图.png]]

![流程概览](旧附件/image-001.png "步骤说明")
→ ![[raw/领域/资料名称/image-001.png]]（图片说明：流程概览；标题：步骤说明）
```

- 媒体嵌入、Markdown 图片及 raw PDF 附件链接按正文顺序统一清点，Markdown 转换无需另行确认。支持中文、编码空格、尖括号目标和合法转义；Markdown 路径只解码一次，Obsidian 文件名保持字面值。按实际文件名匹配目标目录直属文件；短名在其他目录重名时，以指定目录消歧，不递归搜索或猜测改名。
- 保留媒体位置数量、顺序及原有 Obsidian 宽度、别名和片段后缀。Markdown 图片的有意义纯文本 alt/title 转为紧随图片的可见说明，空 alt 或仅为文件名的 alt 不增加说明；不保留原 HTML 的 alt/title 属性呈现方式。除下述 PDF 转换及旧节删除外，普通链接、代码示例、修改跨度外的正文及 raw 文件不变。
- **PDF 附件嵌入化**：正文中的 `[讲义](<../../raw/示例/资料/讲义.pdf>)` 或 `[讲义](<raw/示例/资料/讲义.pdf>)`，在指定 raw 目录直属文件中唯一确认后改为 `![[raw/示例/资料/讲义.pdf]]`；安全片段保留，原链接文字及可选标题只保留在报告中。已合规的 PDF 嵌入不动；缺失、歧义、越界、不安全语法或有效指向其他 raw 目录的链接保持原样并报告，不读取 PDF 内容。
- **旧节清理**：仅本命令删除正文二级标题文本 trim 后精确为「总结」或「洞察」的节，从标题行至下一个真实二级标题之前或 EOF；相邻、重复候选逐节处理，不匹配「资料总结」「洞见」等名称，也不匹配代码、注释中的标题。节内含 Obsidian 嵌入、Wiki 链接、Markdown 图片或 PDF 附件链接时拒删并报告，其他安全引用修复继续。本命令不新增任何内容节，`enhance-wiki-content` 全部机制不变。
- 外部 URL、引用式或 HTML 图片、外层链接包裹的图片、复杂说明及其他不安全语法保持原样并报告，不下载媒体或改引用定义。目标缺失、无法唯一匹配或已有效显式指向其他 raw 目录时也不替换。详见 [解析规则和匿名验收案例](references/raw-reference-validation.md)。
- Frontmatter 缺整块或缺任一标准字段时补齐七字段；缺失的 `updated` 用当日日期，已有字段（包括非标准字段）与 `sources` 保留，仅在页面实质变化时刷新已有 `updated`，包括 PDF 转换或旧节删除。来源失效或未覆盖目标目录只报告；已有 frontmatter 无法安全解析时停止并保持零写入。
- 索引未收录才补录，重算六变量并校验页脚；已有条目只验证，不因分区不同重复新增。该命令的窄维护范围优先于通用自动修复规则。
- 只有实际文件变化才运行日志预检并追加一次最终记录；重复执行无变化时不改日期、不写日志、不分卷。
- 写入工具必须保留修改跨度外的原换行符、末尾换行状态和日志历史前缀；只有授权删除到 EOF 本身带来的末尾状态变化允许保留。若工具不能保留 CRLF 或无末尾换行等原始格式，停止写入并报告，不为继续操作而统一转换换行符。

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

目录批次的真实页面名称、raw 配对、展开清单、跳过/失败原因和测试运行产物同样不得公开。公开目录示例与验收案例只使用虚构名称，不能照抄已经执行过的私人课程任务。

`query-image` 的输入截图、识别文本、manifest 和真实查询结果同样属于查询资料，不得加入公开 commit 或 PR；公开示例只使用虚构内容和路径占位符。图片默认不入库，并不代表图片不会经过模型服务处理；视觉 MCP 必须遵守已有的数据传输授权，不会为查询自动启用新的外部上传服务。

`update-raw-reference` 仅修复本地引用，不上传媒体。公开示例必须使用占位符或虚构资料，不提交真实媒体路径、页面正文、manifest、操作日志或测试库。

`enhance-wiki-content` 的公开示例只使用占位符或虚构资料。真实输入页面、图文提炼结果、图片清单、日志及验证用知识库不进入公开 commit 或 PR；引用过往任务不代表获准公开其中的内容。

## 视频阅读（默认启用）

`ingest`、`optimize` 和带 raw 目录的 `enhance-wiki-content` 默认读取范围内的视频；仅给页面的文末增强继续只使用既有正文。可加 `--no-video` 关闭视频探测、抽帧、视觉读取及附属字幕查找，保留媒体引用与清单位置，并继续分析图片和正文。该参数可与 `--defer` 任意顺序组合，均放在位置参数之前。

```text
$obsidian-llm-wiki enhance-wiki-content "wiki/<领域>/<页面>.md" "raw/<领域>/<资料>/"
$obsidian-llm-wiki enhance-wiki-content --no-video "wiki/<领域>/<页面>.md" "raw/<领域>/<资料>/"
$obsidian-llm-wiki optimize --defer --no-video "wiki/<领域>/<页面>.md"
```

Codex 未提供经验证的视频直读工具时，使用已有 ffprobe/ffmpeg 本地抽帧，再以现有看图能力分析。默认每 5 秒抽帧、每个视频最多 60 帧；长视频均匀扩大间隔，并披露可能遗漏的短暂画面。识别画面与可见字幕，可读取范围内明确对应的已有 SRT/VTT；不进行语音转写。单个视频失败只影响该条目，无可用证据时不写入内容。

固定脚本只使用 Python 标准库，不自动安装工具或修改 PATH。真实抽帧时间、来源哈希与清理清单只保存在任务临时目录，按既有清单逐文件清理。抽帧本地完成，视觉分析仍使用当前模型服务。视频、字幕、抽帧、真实路径/哈希、清单和日志不得公开。详见 [视频读取规则](references/video-reading.md)。

## License

MIT License. See `LICENSE`.
