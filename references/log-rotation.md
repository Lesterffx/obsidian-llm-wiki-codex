# Log Rotation

仅在用户显式调用 `log` 工作流，或 `scripts/log-preflight.ps1` 返回 `rotation_due=true` 时读取本参考。

## 接口

- `log status`：以 `-Detailed -Json` 运行预检脚本；只读，不执行轮转。
- `log query "<条件>"`：使用 `rg` 搜索 `log.md` 和 `logs/archive/*.md`，只读取命中附近的有限内容。
- `log rotate now`：不考虑日期和大小，立即轮转。
- `log rotate year`：仅当活动日志起始年份早于当前年份时轮转。
- `log rotate size`：仅当投影字节数达到阈值时轮转。
- `log rotate auto`：跨年或达到阈值时轮转。

只读 query、只读 audit/lint、`log status`、`log query` 和没有文件变化的任务不得自动轮转。写入任务追加唯一最终日志前，把包含分隔符和末尾换行的实际待追加文本传给预检脚本。

## 标准条目

保留既有标题契约：

```markdown
## [YYYY-MM-DD] <action> | <title>

- 范围：本次任务及边界。
- 变更：涉及的文件和操作。
- 资料：来源、图片或附件核对结果。
- 维护：frontmatter=<valid/repaired/n-a>；index=<unchanged/refreshed>；schema=<unchanged/updated, hash-equal>；raw=unchanged。
- 验证：实际执行的检查及结果。
- 未决：存在异常时填写。
```

`范围`、`变更`、`维护`、`验证`为必需字段。仅在涉及来源或媒体时写`资料`，仅在存在未解决事项时写`未决`。`index.md` 发生变化时，在`维护`中记录六变量。不得为匹配新格式而改写旧条目。

## 分卷结构

```text
log.md
logs/
|-- log-archives.md
`-- archive/
    `-- log-YYYY-MM-DD-to-YYYY-MM-DD.md
```

`log.md` 是唯一活动日志；`logs/archive/` 下的文件不可修改。`logs/` 位于 `wiki/` 之外，不计入 `index.md` 页面统计。

首次实际轮转时才创建 `logs/log-archives.md`：

```markdown
# Log Archives

> 历史日志分卷清单。归档文件只读，不得修改或继续追加。

| Archive | Period | Entries | Bytes | SHA-256 | Trigger | Archived |
|---|---|---:|---:|---|---|---|
```

每次成功轮转只在表格末尾增加一行，不重写或重排已有记录。

## 轮转流程

1. 完成任务并构造唯一最终日志条目；操作前立即重新运行预检。
2. 只读取确定首尾 `## [YYYY-MM-DD]` 标题所需的元数据和有限内容；统计标题时不得把日志正文返回模型上下文。
3. 记录活动日志的准确字节数、条目数、最后修改时间和 SHA-256；归档目标已经存在时停止。
4. 按验证后的日期范围使用 `logs/archive/log-YYYY-MM-DD-to-YYYY-MM-DD.md`；仅在第一次实际轮转时创建 `logs/` 和 `logs/archive/`。
5. 使用明确的 literal path 移动整份活动日志；不得复制后清空、拆分条目、改写历史、使用通配符或覆盖目标。
6. 要求归档后的字节数、条目数和 SHA-256 与移动前完全一致。
7. 用 `assets/log-active.md` 创建新的 `log.md`，不得复制旧条目、摘要或尾部内容。
8. 创建或追加 `logs/log-archives.md`，记录归档路径、时间范围、条目数、字节数、完整 SHA-256、触发原因和归档日期。
9. 自动轮转作为其他写入任务的一部分时，将归档信息写进该任务唯一的最终条目，不增加第二条 `rotate` 记录；显式轮转任务写一条标准 `rotate` 记录。
10. 验证新日志格式、分卷目录行、末尾换行、唯一任务标题和归档哈希。

如果移动前发现元数据或哈希并发变化，丢弃旧计划并重新推导。轮转失败但原 `log.md` 仍完整时，把任务条目追加到原日志并标记`轮转待处理`。移动成功但新日志创建失败时，只有在目标不存在且归档长度和哈希仍匹配时，才能把归档恢复为 `log.md`；否则停止并报告准确状态，绝不覆盖任一路径。

## 低 Token 追加

普通追加可在 PowerShell 内部读取 `-Tail 80`，仅在必要时扩大到200行。只向模型返回：

- 原始字节数、SHA-256和最后修改时间；
- 有限尾部中是否已经存在完全相同的任务标题；
- 用作 `apply_patch` EOF锚点的最后2–4行。

不得把完整尾部返回模型上下文。追加后只返回唯一标题计数、长度增量、原始前缀哈希结果、末尾换行结果，以及新条目是否位于最终位置。

## 备份边界

分卷只是日志整理，不是独立备份。不得自动删除、压缩、合并或继续追加历史卷；真正的备份必须位于单独管理的备份位置。
