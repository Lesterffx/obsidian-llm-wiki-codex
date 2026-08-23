# 隐私与公开发布检查

这个仓库只应该包含通用 Codex Skill、模板和说明文档。不要把你的个人 Obsidian vault 或任何原始资料上传到公开仓库。

## 不要上传的内容

- `raw/`：PDF、DOCX、PPTX、图片、截图、扫描件、课程资料、会议资料。
- `wiki/`：个人知识库页面、客户资料、课程笔记、商业分析、私人总结。
- 项目级配置：私有 vault 的 `AGENTS.md`、`CLAUDE.md`、`index.md`、`log.md`。
- 日志分卷：私有 vault 生成的 `logs/`、`logs/log-archives.md` 和 `logs/archive/*.md`。
- Python 环境：`.venv/`、`.runtime/`、`.codex-python/`。
- Codex 或 Claude 本地目录：`.codex/`、`.claude/`。
- 密钥和账号：API key、token、cookie、密码、SSH key、OAuth 凭证。
- 本机信息：个人用户名、本机绝对路径、网盘路径、客户名称、内部项目名。
- 临时文件：缓存、日志、导出中间产物、系统文件。

## 发布前检查

建议每次 push 前做这些检查：

```powershell
rg --files
```

确认只包含公开文件，例如：

```text
SKILL.md
README.md
LICENSE
PRIVACY.md
.gitignore
agents/openai.yaml
assets/*.md
examples/*.example.md
references/index_stat.py
references/log-rotation.md
references/schema.md
scripts/log-preflight.ps1
```

搜索敏感词和私有路径时，重点检查密钥、账号凭证、本机绝对路径、网盘目录、真实 raw/wiki 领域名和客户/课程名称。

如果命中内容来自个人 vault、原始资料、本机路径或密钥，请先移除再发布。文档中的泛化安全提醒可以保留，真实凭证和真实路径不能保留。

公开工具脚本必须保持通用：不得内嵌真实 vault 路径、用户名、领域名称、统计数字、客户或课程信息，也不得包含任何账号凭证。日志示例和分卷说明只能使用日期、路径和计数占位符，不得复制真实 `log.md` 条目或归档目录。

## 推荐做法

- 只发布通用模板，不发布你的真实知识库。
- README 中可以使用 `<你的 vault>`、`raw/<领域>/`、`wiki/<领域>/` 这类占位符。
- 公开实战手册只使用占位符，或使用与 `examples/AGENTS.example.md` 一致的虚构领域、目录和页面名称；不要保留真实课程名、客户名、内部项目名、私人页面或本机绝对路径。
- 真实项目规则请留在自己的 Obsidian vault 中，不要上传到公开 repo。
- 如果不确定某个文件是否能公开，默认不要上传。
