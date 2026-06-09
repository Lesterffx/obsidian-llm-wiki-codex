# 隐私与公开发布检查

这个仓库只应该包含通用 Codex Skill、模板和说明文档。不要把你的个人 Obsidian vault 或任何原始资料上传到公开仓库。

## 不要上传的内容

- `raw/`：PDF、DOCX、PPTX、图片、截图、扫描件、课程资料、会议资料。
- `wiki/`：个人知识库页面、客户资料、课程笔记、商业分析、私人总结。
- 项目级配置：私有 vault 的 `AGENTS.md`、`CLAUDE.md`、`index.md`、`log.md`。
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
references/schema.md
```

搜索敏感词和私有路径时，重点检查密钥、账号凭证、本机绝对路径、网盘目录、真实 raw/wiki 领域名和客户/课程名称。

如果命中内容来自个人 vault、原始资料、本机路径或密钥，请先移除再发布。文档中的泛化安全提醒可以保留，真实凭证和真实路径不能保留。

## 推荐做法

- 只发布通用模板，不发布你的真实知识库。
- README 中可以使用 `<你的 vault>`、`raw/<领域>/`、`wiki/<领域>/` 这类占位符。
- 真实项目规则请留在自己的 Obsidian vault 中，不要上传到公开 repo。
- 如果不确定某个文件是否能公开，默认不要上传。
