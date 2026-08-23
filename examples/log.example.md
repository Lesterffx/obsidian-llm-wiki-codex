# 操作日志

> 这是 LLM Wiki 的 append-only 操作日志范例。复制到你的 Obsidian vault 根目录后重命名为 `log.md`。
> 不要删除或修改已有条目；历史分卷入口为 `[[logs/log-archives|Log archives]]`。
> 格式：`## [YYYY-MM-DD] <action> | <title>`；必需字段为范围、变更、维护、验证。

## [YYYY-MM-DD] init | 初始化 LLM Wiki

- 范围：初始化通用 Obsidian LLM Wiki 目录、schema、索引和活动日志。
- 变更：创建 `raw/`、`wiki/`、`AGENTS.md`、`index.md` 和 `log.md`。
- 维护：frontmatter=n-a；index=initialized；schema=initialized；raw=unchanged。
- 验证：确认初始化文件存在、Markdown 格式有效且 `log.md` 以换行结束。

## [YYYY-MM-DD] <action> | <title>

- 范围：<本次任务和边界>。
- 变更：<涉及的文件和操作>。
- 资料：<仅在涉及来源、图片、视频或附件时填写>。
- 维护：frontmatter=<valid/repaired/n-a>；index=<unchanged/refreshed，必要时记录六变量>；schema=<unchanged/updated, hash-equal>；raw=unchanged。
- 验证：<实际执行的检查和结果>。
- 未决：<仅在存在异常、缺失或待处理事项时填写>。

`范围`、`变更`、`维护`、`验证`为必需字段；`资料`、`未决`按需出现，不保留空占位符。追加前使用固定预检脚本判断投影大小与跨年状态，并检查重复任务标题、文件长度、SHA-256、末尾内容和更新时间；通过 `apply_patch` 一次追加。追加后验证文件长度增加、完整条目位于末尾、结尾仍有换行，且追加前长度范围的前缀 SHA-256 未变化。

默认在投影大小达到 2 MiB 或活动日志跨年时整卷归档。轮转采用完整移动，不拆分或重写历史内容；新 `log.md` 使用 Skill 的 `assets/log-active.md`，历史卷保存在 `logs/archive/`，目录记录在 `logs/log-archives.md`。分卷不是独立备份。
