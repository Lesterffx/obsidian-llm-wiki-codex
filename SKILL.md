---
name: obsidian-llm-wiki
description: Maintain Obsidian LLM Wiki knowledge bases in Codex. Use when working with Obsidian vaults that have raw/ and wiki/ layers, AGENTS.md or CLAUDE.md schema files, index.md, and log.md; when the user asks to ingest source material, preprocess PDF/DOCX/PPTX files with a project Python venv, analyze raw images or screenshot courses, process PPT screenshots, read wiki image embeds, batch-analyze many images with default subagents, query the wiki, lint or audit wiki health, migrate notes, delete or remove wiki pages, rebuild the index, check AGENTS.md/CLAUDE.md/index.md freshness, normalize YAML frontmatter and tags, optimize existing wiki pages, append summaries, extract thinking frameworks, or organize Chinese knowledge-base pages.
---

# Obsidian LLM Wiki

Use this skill to maintain an Obsidian knowledge base where `raw/` is the immutable source layer and `wiki/` is the LLM-maintained knowledge layer.

## Grounding

Before acting, read the vault schema:

1. Prefer `AGENTS.md` in the vault root.
2. If `AGENTS.md` is absent, read `CLAUDE.md`.
3. Read `index.md` before answering knowledge queries or choosing related pages.
4. Read `log.md` only when recent changes, history, or operation format matters.

If both `AGENTS.md` and `CLAUDE.md` exist and conflict, follow `AGENTS.md` for Codex behavior and note the conflict when it affects the task.

## Safety Rules

- Never modify, move, rename, or delete anything under `raw/`.
- Never use recursive, wildcard, piped, looped, or bulk deletion commands.
- If a single file must be deleted, use only `Remove-Item -LiteralPath "<absolute file path>"` after confirming it is one file, not a directory, with no wildcard and no `-Recurse`.
- Do not overwrite existing wiki content unless the user explicitly asks for overwrite. For optimization tasks, preserve existing content and image embeds unless the user requests restructuring.
- Keep `log.md` append-only.
- Keep Chinese as the primary content language unless the user asks otherwise.
- Preserve existing Obsidian links and image embeds. Do not remove `![[image.png]]` embeds during page optimization.
- For image-heavy work, build an image manifest first and use the batch workflow below. Ask only when image scope, ordering, or duplicate filenames cannot be resolved from the page and its sources.
- Use short Obsidian image embeds such as `![[文件名.png]]`; do not convert them to full paths.

## Windows And Python

Work in PowerShell with Unicode-safe paths.

- Prefer `rg` for file discovery.
- Do not rely on system `python`, `py`, or `python3`.
- Prefer the current vault or project `.venv\Scripts\python.exe` when it exists.
- For project scripts, prefer in order: `.venv\Scripts\python.exe`, `.runtime\python\python.exe`, `.codex-python\python.exe`.
- Use `pathlib.Path` in any Python script created for this workflow.
- Pass Chinese paths as explicit PowerShell arguments; do not pipe Chinese paths or content into Python.
- Do not modify Windows PATH, install Python, remove Python versions, or call user-directory Python unless the user explicitly asks.

## Document Preprocessing Runtime

For PDF, DOCX, PPTX, spreadsheet, and image-manifest preprocessing, use the vault or project virtual environment when available:

```powershell
& ".\.venv\Scripts\python.exe" ".\scripts\<script>.py" "<input-path>" "<output-path>"
```

The project venv is for deterministic preprocessing only:

- Extract text and metadata from DOCX, PDF, PPTX, and XLSX files.
- Extract or enumerate embedded images, slide/page order, filenames, dimensions, and source document references.
- Render PDF pages or PPTX slides to image files only when the user explicitly asks for generated outputs.
- Build ordered manifests for later default-agent visual analysis.
- Keep generated intermediate outputs outside `raw/` unless the user explicitly asks to add new source assets there.

Use `default` agents for visual understanding after preprocessing:

- The venv handles repeatable parsing, ordering, and manifest creation.
- Default agents handle OCR-like reading, screenshot interpretation, diagrams, UI details, and conceptual synthesis.
- Traditional OCR engines such as Tesseract, OpenCV, PaddleOCR, or RapidOCR are not assumed available unless the user explicitly adds them.

## Templates

Use project-local `templates/` first if present. Otherwise use this skill's templates:

- `assets/wiki-page.md` for general pages.
- `assets/book-note.md` for book notes.
- `assets/meeting-note.md` for meetings.
- `assets/tool-page.md` for tool pages.

For new vault initialization, use `examples/AGENTS.example.md`, `examples/index.example.md`, and `examples/log.example.md` when available; use `references/schema.md` as the fuller schema reference.

Use `references/schema.md` only when initializing or repairing a vault schema. For existing vaults, the project `AGENTS.md` or `CLAUDE.md` is authoritative.

## Frontmatter And Tag Normalization

For every wiki create, update, or optimization task, check note properties before writing content:

- Every wiki page must start with YAML frontmatter containing `title`, `created`, `updated`, `domain`, `tags`, `sources`, and `status`.
- If frontmatter is missing, add it before the existing content. Infer conservative values from the filename, schema path, current date, declared sources, and current page state; ask only when domain or source cannot be inferred safely.
- If frontmatter exists but fields are missing or stale, repair missing fields and update `updated` to the current date when the page content or tags change.
- Treat frontmatter `tags` as authoritative. When inline tags are present, make them match the normalized frontmatter tags.
- Normalize only tag values: trim whitespace and replace internal spaces inside each tag segment with `_`. Examples: `AI Live` becomes `AI_Live`; `一堂/AI Live` becomes `一堂/AI_Live`.
- Apply tag normalization to frontmatter `tags` and inline hashtags such as `#一堂/AI Live` or `` `#一堂/AI Live` ``.
- Do not automatically rename or rewrite `domain`, `sources`, raw paths, wiki paths, directory names, filenames, page titles, wiki links, image embeds, or ordinary prose just because they contain spaces.

## Schema And Index Freshness Check

Every time this skill is used, consider whether `AGENTS.md`, `CLAUDE.md`, and `index.md` remain current. They do not need to change every time, but they must be checked.

- Check `AGENTS.md` for domain registry, raw/wiki path registration, processing rules, safety rules, tag rules, image/document rules, and workflow changes that may need Codex-facing schema updates.
- Check `CLAUDE.md` for shared schema content that should stay compatible with `AGENTS.md`.
- Check `index.md` for page additions, deletions, migrations, renames, path changes, summary changes, tag changes, and stale or missing entries.
- For read-only tasks such as query, audit, or exploratory analysis, report whether these files appear to need updates; do not modify them unless the user asks for fixes.
- For any task that changes files, append `log.md` with the check result for all three files, even when the result is `已检查，无需更新`.
- Default agents and other subagents may help analyze content, but the main Codex agent must own this freshness check and all writes.

## Image-Heavy Source Analysis

Use this workflow for raw image directories, screenshot courses, PPT screenshot exports, or wiki pages whose Markdown references raw images with `![[...]]`.

1. Build an image manifest before analysis:
   - For a wiki page, extract every `![[...]]` embed in document order.
   - Prefer the page's `sources` raw directories when resolving short image names.
   - If `sources` is empty or incomplete, search the vault by exact filename and report unresolved or ambiguous matches.
   - For a raw directory, include image files in natural filename order unless a wiki page gives a different embed order.
   - For PDF, DOCX, or PPTX sources, use `.\.venv\Scripts\python.exe` to inspect text, embedded media, page or slide order, and document metadata before assigning images to batches.
2. Preserve order:
   - Existing wiki embed order is authoritative.
   - Raw-only image sets use natural filename order.
   - Do not reorder embeds in the page while optimizing unless the user explicitly asks.
3. Detect coverage risks:
   - Report duplicate filenames, missing files, non-image embeds, and images outside declared `sources`.
   - Do not guess which duplicate image is intended.
4. Keep analysis traceable:
   - Store intermediate notes in the working context or final response, not in `raw/`.
   - When writing wiki content, identify images by filename and, when helpful, by their manifest index.

## Default Agent Batch Analysis

When the user explicitly asks for default agents, subagents, or parallel agent work, use `multi_agent_v1.spawn_agent` with `agent_type: "default"` for read-only image analysis. The main Codex agent owns manifest creation, batching, final synthesis, and all file writes.

Batching defaults:

- 1-10 images: analyze locally unless delegation is useful.
- 11-30 images: split into 2-3 default agents.
- 31+ images: split into up to 6 default agents.
- 100+ images: start with up to 6 parallel batches; if a batch remains too large, continue with later sub-batches after the first round returns.

Subagent rules:

- Subagents only read images and return analysis. They must not modify `raw/`, `wiki/`, `index.md`, `log.md`, or schema files.
- Pass each subagent a bounded manifest slice with absolute image paths and stable manifest indexes.
- Use `items` with `local_image` entries when dispatching images that need visual inspection.
- Do not send the same image to multiple subagents unless validating an uncertain reading.
- After subagents return, compare returned filenames and indexes against the manifest before synthesizing.

Subagent output contract:

- Per image: manifest index, filename/path, visible text, page topic, key points, diagrams/flows/UI elements, extractable insights, confidence, and unreadable or uncertain areas.
- Per batch: batch summary, repeated ideas, contradictions or low-confidence readings, and candidates for wiki sections such as `图片内容解析`, `洞见`, `方法论提炼`, `最佳实践`, and `金句精选`.

Prompt shape for a default subagent:

```text
Analyze this image batch for an Obsidian LLM Wiki update. Read only. Do not edit files.
Return one section per image using the required output contract, then a batch summary.
Preserve manifest indexes and filenames exactly.
```

## Workflows

### Ingest

Use when the user gives a new source under `raw/`.

1. Confirm the source path is under the correct `raw/` domain and never edit it.
2. Read the source with the appropriate file skill or tool. For PDFs, DOCX, PPTX, and image-heavy folders, inspect actual content rather than guessing from filenames.
3. For PDF, DOCX, PPTX, and spreadsheet sources, use the project venv for deterministic preprocessing when local parsing is needed.
4. For image-heavy sources, build an image manifest and use the batch analysis workflow before drafting the wiki page.
5. Map the source to the correct wiki path from the schema.
6. Create or update a wiki page with normalized frontmatter, inline tags, a one-sentence summary, body content, `## 相关`, and `## 来源`.
7. Integrate image analysis into useful sections such as `资料总结`, `图片内容解析`, `洞见`, `方法论提炼`, `最佳实践`, and `金句精选`.
8. Add at least two meaningful wiki links when possible.
9. Update affected related wiki pages only when the new information materially changes cross-links, contradictions, or summaries.
10. Check and update `AGENTS.md`, `CLAUDE.md`, and `index.md` as needed, then append `log.md` with all three freshness results.
11. If a top-level raw/wiki directory is not registered in the schema, report it and ask before changing schema files.

### Query

Use when the user asks a question about the knowledge base.

1. Read `index.md` to locate candidate pages.
2. Read the most relevant wiki pages.
3. Synthesize the answer in Chinese and cite pages with `[[页面标题]]`.
4. Consider whether `AGENTS.md`, `CLAUDE.md`, or `index.md` appear stale and mention material findings in the answer.
5. If the answer is worth preserving, suggest archiving it as a wiki page, but do not create one without user confirmation.

### Optimize Existing Wiki Pages

Use when the user asks to optimize, reorganize, add frontmatter, add summaries, or improve a specific wiki page.

1. Read the page and its declared `sources`.
2. Check whether YAML frontmatter exists and whether it contains all required note properties.
3. Preserve all existing image embeds and their order.
4. If the page contains image embeds or image-heavy sources, build an image manifest, resolve images from raw sources, and analyze coverage before writing.
5. If default agents are used, verify every manifest index has an analysis result or an explicit unresolved note before synthesis.
6. If the user says "不修改现有内容", append new material before `## 相关` and leave existing sections intact.
7. Add or repair YAML frontmatter, inline tags, one-sentence summary, related links, and source citations.
8. Add useful sections such as `资料总结`, `图片内容解析`, `洞见`, `方法论提炼`, `最佳实践`, `金句精选`, or quick-reference tables when they fit the material.
9. Check and update `AGENTS.md`, `CLAUDE.md`, and `index.md` as needed, then append `log.md` with all three freshness results.

### Extract Thinking Frameworks

Use when the user asks to create or expand pages under `wiki/提炼思维/`.

1. Read all requested source wiki pages or directories.
2. Extract reusable patterns, mental models, workflows, best practices, pitfalls, and memorable lines.
3. Create or update a page under `wiki/提炼思维/` with no raw source layer unless the schema specifies one.
4. Link back to the source wiki pages, check `AGENTS.md`, `CLAUDE.md`, and `index.md`, and append `log.md` with all three freshness results.

### Lint Or Audit

Use for health checks and maintenance.

Check for missing frontmatter, mismatched inline/frontmatter tags, broken wiki links, orphan pages, empty sources, unregistered raw/wiki directories, stale pages, duplicate index entries, and contradictions across related pages. Report findings first. Only modify files if the user asks for fixes.

Also report whether `AGENTS.md`, `CLAUDE.md`, or `index.md` need updates. If the lint or audit task changes files, append `log.md` with all three freshness results.

### Index

Use when the user asks to rebuild or refresh `index.md`.

Scan `wiki/` markdown files, read frontmatter and summary lines, group pages by schema domains, preserve useful existing organization when possible, and append a `log.md` entry if `index.md` changes.

When rebuilding or refreshing `index.md`, also check whether scanned paths reveal missing domain registrations or stale rules in `AGENTS.md` or `CLAUDE.md`.

### Migrate

Use for one-time migration of existing notes into the LLM Wiki structure.

Identify markdown files outside `raw/` and `wiki/`, ask for domain placement when not obvious, then move by explicit user-approved paths only. Avoid bulk operations. Preserve content, add frontmatter, update links, rebuild `index.md`, and append `log.md`.

Before and after migration, check `AGENTS.md`, `CLAUDE.md`, and `index.md` for path, domain, and summary freshness. Record all three results in `log.md` when files are changed.

### Delete Or Remove Wiki Pages

Use only when the user explicitly asks to delete, remove, archive, or de-index wiki content.

1. Never delete anything under `raw/`.
2. Prefer archiving or de-indexing over deletion unless the user clearly asks for physical deletion.
3. If a wiki file must be deleted, delete only one explicit file path at a time with the safe Windows deletion rule above.
4. Check whether related links, backlinks, `index.md`, `AGENTS.md`, or `CLAUDE.md` need updates after the removal.
5. Append `log.md` with the deletion/removal action and the freshness result for `AGENTS.md`, `CLAUDE.md`, and `index.md`.

## Page Requirements

Every wiki page should contain:

1. YAML frontmatter with `title`, `created`, `updated`, `domain`, `tags`, `sources`, and `status`.
2. Inline tags matching frontmatter tags when inline tags are used.
3. Tags normalized so spaces inside tag segments become `_`, such as `一堂/AI_Live`.
4. A one-sentence summary in blockquote form.
5. Main content.
6. `## 相关` with meaningful wiki links.
7. `## 来源` pointing to raw directories or files, except schema-defined no-raw domains such as extracted thinking pages.

Use the current date from the environment for `created`, `updated`, and log entries.
