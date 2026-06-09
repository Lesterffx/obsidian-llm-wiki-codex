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

Codex 版在这个思路上做了进一步适配：它可以结合项目内 Python 虚拟环境做 PDF/DOCX/PPTX 等文档预处理，也可以通过 image manifest 和最多 6 个 default agents 分批分析大量图片、截图课程和 PPT 页面。主 Codex 负责核对覆盖率、整合结果、写入 wiki、维护索引和追加日志。

## 三层架构设计

```text
┌─────────────────────────────────────────┐
│ Schema                                  │
│ AGENTS.md 优先；缺失时兼容 CLAUDE.md     │
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
- `AGENTS.md`：Codex 优先读取的项目 schema，定义领域、目录、frontmatter、标签、工作流和安全规则。
- `CLAUDE.md`：可选兼容文件。如果项目没有 `AGENTS.md`，Skill 会回退读取 `CLAUDE.md`。
- `index.md`：知识库目录，由 LLM 按 wiki 当前状态维护。
- `log.md`：操作日志，append-only。

## Codex 版功能特点

- **AGENTS.md 优先**：更适配 Codex 项目规则；没有 `AGENTS.md` 时兼容 `CLAUDE.md`。
- **frontmatter 与标签规范化**：新增、修改、优化 wiki 页面时检查 YAML frontmatter；tag 中空白会规范为 `_`。
- **schema/index freshness check**：每次执行 Skill 都考虑 `AGENTS.md`、`CLAUDE.md`、`index.md` 是否需要更新。
- **文档预处理运行时**：优先使用项目 `.venv` 处理 PDF、DOCX、PPTX、XLSX 的文本、页序、slide 顺序、图片 manifest。
- **图片密集资料分析**：先建立 image manifest，再处理截图课程、PPT 截图、raw 图片目录和 wiki 图片引用。
- **最多 6 个 default agents 批量读图**：大量图片可拆成最多 6 个并行批次，只读分析后由主 Codex 汇总。
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
│   └── tool-page.md
├── references/
│   └── schema.md
├── README.md
├── PRIVACY.md
├── LICENSE
└── .gitignore
```

## 安装方式

将本仓库中的 Skill 目录放到你的 Codex skills 目录：

```powershell
%USERPROFILE%\.codex\skills\obsidian-llm-wiki
```

建议目录结构：

```text
%USERPROFILE%\.codex\skills\obsidian-llm-wiki\
├── SKILL.md
├── agents/
├── assets/
└── references/
```

安装后重启 Codex，或新开一个 Codex 线程，让 Skill 元数据重新加载。

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

如果你已经有 Claude Code 版 `CLAUDE.md`，可以先继续兼容使用；Codex 版更推荐逐步迁移或同步一份 `AGENTS.md`。

### 2. 初始化 schema

可以参考 `references/schema.md` 创建项目级 `AGENTS.md`。它应该描述：

- raw/wiki 目录结构
- 领域注册表
- frontmatter 规范
- 标签体系
- wiki 链接规则
- 图片管理规则
- 变更联动规则
- ingest/query/lint/migrate/index 工作流

### 3. 放入原始资料

把 PDF、DOCX、PPTX、网页剪藏、截图、课程图片等放入 `raw/<领域>/`。

`raw/` 是事实来源和附件层，默认只读。

### 4. 调用 Skill

示例：

```text
$obsidian-llm-wiki ingest @raw/AI/某课程/
```

```text
$obsidian-llm-wiki query “这个知识库里关于 AI 编程出海的核心方法论是什么？”
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
$obsidian-llm-wiki 优化 @wiki/路径/页面.md，图片很多。请先建立 image manifest，保持图片顺序，必要时调用最多 6 个 default agents 分批只读分析。
```

### PDF / DOCX / PPTX

```text
$obsidian-llm-wiki ingest @raw/路径/文件.pptx，先做文档预处理，确认 slide 顺序、文本和图片 manifest，再整理成 wiki 页面。
```

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
| 主要 schema | `CLAUDE.md` | `AGENTS.md` 优先，缺失时兼容 `CLAUDE.md` |
| Agent 能力 | Claude Code 工作流 | Codex 主 agent + default agents 批量图片分析 |
| 文档预处理 | 以 Claude 工作流为主 | 支持项目 `.venv` 做确定性预处理 |
| 图片处理 | 保留图片引用，按需分析 | image manifest + 最多 6 个 default agents |
| 适用环境 | Claude Code | Codex / Codex App |

## 隐私与安全

不要把以下内容上传到公开仓库：

- 你的 Obsidian vault。
- `raw/` 原始资料、截图、课程文件、扫描件。
- `wiki/` 中包含个人、客户、课程或商业隐私的页面。
- 项目级 `AGENTS.md`、`CLAUDE.md`、`index.md`、`log.md`。
- `.venv/`、缓存、临时文件。
- API key、token、cookie、密钥、账号信息。
- 本机绝对路径和个人目录结构。

本仓库只发布通用 Skill 和模板，不包含任何个人知识库资料。

更多检查清单见 `PRIVACY.md`。

## License

MIT License. See `LICENSE`.
