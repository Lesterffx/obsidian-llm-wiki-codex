# 操作日志

> 这是 LLM Wiki 的 append-only 操作日志范例。复制到你的 Obsidian vault 根目录后重命名为 `log.md`。不要删除历史日志，只在末尾追加新记录。日志较大时只读取末尾 80 行，必要时最多 200 行；使用唯一 EOF 锚点安全追加，不整文件读取或重写。

## [YYYY-MM-DD] init | 初始化 LLM Wiki

- 页面：`AGENTS.md` / `index.md` / `log.md`
- 操作：初始化 Obsidian LLM Wiki 结构
- 变更：
  - 创建 `raw/` 与 `wiki/` 目录结构
  - 创建项目 schema `AGENTS.md`
  - 创建内容索引 `index.md`
  - 创建 append-only 操作日志 `log.md`
- `AGENTS.md`：已更新，初始化项目 schema
- `CLAUDE.md`：无需更新，当前仅使用 Codex `AGENTS.md`
- `index.md`：已更新，初始化空索引

## [YYYY-MM-DD] <操作类型> | <标题>

- 页面：`wiki/<领域>/<页面标题>.md`
- 操作：<ingest / optimize / lint / audit / query / migrate / index / delete/remove>
- 变更：
  - <具体变更 1>
  - <具体变更 2>
- `AGENTS.md`：已检查 / 已更新 / 无需更新，<说明>
- `CLAUDE.md`：已检查 / 已更新 / 无需更新，<说明>
- `index.md`：已检查 / 已更新 / 无需更新，<说明>
- frontmatter：已检查 / 已补到顶部 / 已修复字段 / 只读未写入，<说明>
- index 统计：`indexed_page_count` = N；`wiki_file_count` = N；`registered_domain_count` = N；`missing_count` = N；`broken_count` = N；`duplicate_count` = N；已变化 / 未变化 / 已修正统计漂移，<说明>

追加前检查重复任务标题、文件长度、SHA-256、末尾内容和更新时间；通过 `apply_patch` 一次追加。追加后验证文件长度增加、完整条目位于末尾、结尾仍有换行，且追加前长度范围的前缀 SHA-256 未变化。
