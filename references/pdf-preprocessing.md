# PDF 预处理

本 reference 只规定 PDF 的文本、页码、元数据、图片对象与视觉降级流程。临时文件清理由独立的 [temp-cleanup.md](temp-cleanup.md) 负责；不要把两个工作流合并。

## 固定入口

不要为普通 PDF 任务临时生成另一份预处理脚本。使用 Skill 自带脚本和项目虚拟环境：

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
& ".\.venv\Scripts\python.exe" "<skill_base>\scripts\preprocess_pdf.py" `
  --input "<PDF绝对路径>" `
  --vault-root "<知识库绝对路径>" `
  --task-id "<时间戳-安全任务标识>"
```

- `task-id` 只能包含字母、数字、点、下划线和连字符，且不能是 `.` 或 `..`。
- 输出目录固定为 `<vault-root>/tmp/obsidian-llm-wiki/<task-id>/`。
- 任务目录必须在运行前不存在；脚本拒绝覆盖或复用既有目录。
- 脚本只读取输入 PDF，不修改 `raw/`，也不写入 `wiki/`、`index.md`、`log.md` 或 Schema。

## 提取器分工

- `pypdf` 优先负责中文文本与 PDF 元数据。
- PyMuPDF 负责页数、页面尺寸、嵌入图片对象、xref、图片尺寸与必要的整页渲染。
- 不要因为 PowerShell 终端显示乱码就判断文件损坏；先确保 UTF-8 环境，再检查脚本输出的逐页质量指标。
- 不要把 PyMuPDF 的文本结果默认当作中文正文。它只在 `pypdf` 质量不合格且自身质量更高时作为逐页降级结果。

## 乱码与质量判定

脚本为每页分别记录两个提取器的：

- 字符数；
- `U+FFFD` 替换字符数量与比例；
- 非换行、制表符之外的控制字符数量与比例；
- 连续替换字符或 `���` 片段；
- 最终选择的提取器和状态。

逐页决策：

1. `pypdf` 有文本且未超过异常阈值时，选用 `pypdf`。
2. `pypdf` 不合格时比较 PyMuPDF；只有 PyMuPDF 通过阈值且质量更高时才选用它。
3. 两者文本都为空时，状态为 `empty_text`。
4. 两者都疑似乱码时，状态为 `corrupt_text`。
5. `empty_text` 和 `corrupt_text` 页面自动渲染为 PNG，页面正文位置只写“需视觉读取”，不得把乱码写入 Wiki。

质量检测是风险筛选，不替代内容核对。标题、章节名、关键数字或引用若仍可疑，应回看页面渲染或使用当前可用的视觉通道。

## 固定产物

脚本按需生成：

- `metadata.json`：源文件、SHA-256、PDF 元数据、页数和提取器信息；
- `pages.json`：逐页文本、选择结果、质量指标、图片出现数量和视觉读取状态；
- `page_text.md`：按页组织的可用文本；异常页面只保留视觉读取占位；
- `image_manifest.csv`：每个图片出现位置；
- `unique_image_manifest.csv`：按 xref 去重的图片对象；
- `images/`：唯一嵌入图片对象；
- `rendered_pages/`：只包含文本为空或疑似乱码而需要视觉读取的页面；
- `created_files.json`：本次实际创建的普通文件清单和建议清理顺序。

脚本标准输出返回简洁 JSON 摘要。后续图片分析必须按 manifest 索引对账；不得依赖文件系统返回顺序。

## 使用边界

- 视觉分析结果与 PDF 文本层必须区分；图片推论不能伪装成 PDF 明文。
- 定量数据、引用和发布日期以可核对正文为准；装饰性图表元素不能作为数据证据。
- 完成页面、索引和必要验证后，再进入独立的临时文件清理流程。
