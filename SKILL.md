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

## Mandatory Maintenance Pass

Every use of this skill includes a mandatory maintenance pass. The user does not need to explicitly ask to update `index.md`, repair YAML frontmatter, or sync `AGENTS.md` / `CLAUDE.md`; inspect these automatically and update structural gaps when found.

Explicit user boundaries still win: if the user says read-only, audit-only, query-only, or "do not modify any files", do the same inspection but report the gaps instead of writing changes.

Run this pass before finalizing any task:

1. Read `AGENTS.md`, `CLAUDE.md` when present, and `index.md`.
2. Identify the task-scoped wiki page(s). For ingest, optimize, migrate, delete/remove, and extract-thinking tasks, inspect every page being created, edited, moved, removed, or directly cited as the output. For query tasks, inspect the pages read to answer the query. For lint, audit, or index tasks, inspect the requested scope, or the full vault when no narrower scope is given.
3. Check task-scoped wiki page YAML frontmatter for `title`, `created`, `updated`, `domain`, `tags`, `sources`, and `status`. YAML frontmatter is structural metadata and must start on the first line of the page with `---`; repair missing frontmatter, misplaced frontmatter, or missing fields unless the user explicitly forbids file changes. User requests such as "append-only", "put the new material at the end", "do not change the existing body", or "preserve order" apply to prose, images, and content sections, not to the required frontmatter position.
4. Check `index.md` for task-scoped page additions, removals, migrations, renames, missing entries, stale paths, stale summaries, tag changes, page-count/footer drift, duplicate Markdown entries, and broken Markdown links. Before editing `index.md`, scan `wiki/**/*.md`, read current `index.md` entries, and compute `wiki_file_count`, `indexed_page_count`, and the existing footer count. Determine each task-scoped page state: already indexed, file exists but is not indexed, or index entry exists but the file is missing. When `index.md` changes, refresh the top maintenance note and apply the Index Metadata And Statistics rules for footer date and count handling in the same edit.
5. Check `AGENTS.md` and `CLAUDE.md` for stale or missing domain registrations, raw/wiki path registrations, workflow rules, safety rules, tag rules, and image/document processing rules that affect the current task. Keep them compatible when either one needs a structural update.
6. If any files change, append `log.md` with the task action plus the maintenance results for `AGENTS.md`, `CLAUDE.md`, `index.md`, and frontmatter. State whether frontmatter was already valid, repaired at the top of the page, or blocked by an explicit no-write request. If `index.md` changed, state `wiki_file_count`, `indexed_page_count`, and footer count, and whether the indexed page count changed, stayed unchanged, or was corrected because of footer/statistics drift. If no maintenance change is needed but other files changed, log `已检查，无需更新` for each checked item.
7. Maintenance may update structure and metadata without changing source-derived prose. Do not expand, rewrite, or reinterpret source material merely because the maintenance pass found metadata or index gaps.

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

For every wiki create, update, query, ingest, migrate, index, lint, audit, extract-thinking, or optimization task, check task-scoped note properties as part of the Mandatory Maintenance Pass before finalizing:

- Every wiki page must start with YAML frontmatter on the first line of the file, beginning with `---`, and containing `title`, `created`, `updated`, `domain`, `tags`, `sources`, and `status`.
- If frontmatter is missing or appears after any non-frontmatter content, add or move it before the existing content by default; no separate user approval is needed. Infer conservative values from the filename, schema path, current date, declared sources, and current page state; ask only when domain or source cannot be inferred safely.
- If frontmatter exists but fields are missing or stale, repair missing fields by default and update `updated` to the current date when the page content, tags, or source metadata change.
- YAML frontmatter is a structural maintenance exception. User instructions such as "append-only", "put additions at the end", "do not change existing content", or "preserve order" constrain body prose, images, links, and added sections, but they do not defer or relocate required frontmatter repair. Only explicit read-only, audit-only, query-only, or "do not modify any files" instructions block writing frontmatter changes.
- Treat frontmatter `tags` as authoritative. When inline tags are present, make them match the normalized frontmatter tags.
- Normalize only tag values: trim whitespace and replace internal spaces inside each tag segment with `_`. Examples: `AI Live` becomes `AI_Live`; `domain/AI Live` becomes `domain/AI_Live`.
- Apply tag normalization to frontmatter `tags` and inline hashtags such as `#domain/AI Live` or `` `#domain/AI Live` ``.
- Do not automatically rename or rewrite `domain`, `sources`, raw paths, wiki paths, directory names, filenames, page titles, wiki links, image embeds, or ordinary prose just because they contain spaces.

## Schema And Index Freshness Check

Every time this skill is used, you must inspect and decide whether `AGENTS.md`, `CLAUDE.md`, and `index.md` remain current. They do not need to change every time, but inspection is mandatory and structural gaps should be repaired automatically unless the user explicitly forbids file changes.

- Check `AGENTS.md` for domain registry, raw/wiki path registration, processing rules, safety rules, tag rules, image/document rules, and workflow changes that may need Codex-facing schema updates.
- Check `CLAUDE.md` for shared schema content that should stay compatible with `AGENTS.md`.
- Check `index.md` for page additions, deletions, migrations, renames, path changes, summary changes, tag changes, and stale or missing entries.
- For query or exploratory tasks, do not rewrite source-derived content just because it was read. Do repair clear maintenance gaps found in task-scoped pages or index/schema files unless the user explicitly says read-only, audit-only, query-only, or no file changes.
- For any task that changes files, append `log.md` with the check result for all three files and frontmatter, even when the result is `已检查，无需更新`.
- Default agents and other subagents may help analyze content, but the main Codex agent must own this freshness check and all writes.

## Index Metadata And Statistics

Whenever `index.md` is created, rebuilt, refreshed, or otherwise modified, update both its header metadata and footer statistics in the same change.

- Update the top note in the form `由 LLM 维护。上次更新：YYYY-MM-DD（...）`.
- The top note must include the current date, a concise action summary, and the affected files. When many files are involved, summarize as `A.md、B.md 等 N 个 wiki 页面`.
- Update the footer in the form `_统计：N 个页面 | M 个领域 | 上次更新于 YYYY-MM-DD_`.
- Before editing `index.md`, compute both counts:
  - `indexed_page_count`: the number of unique wiki Markdown pages currently recorded in `index.md`. This is the authority for the footer page count.
  - `wiki_file_count`: the number of actual Markdown files from scanning `wiki/**/*.md`. This is for coverage checks, missing-index discovery, broken-link checks, duplicate detection, and drift diagnosis.
- Count only wiki Markdown pages for `indexed_page_count`. Do not count `.canvas` files, images, raw files, generated preprocessing artifacts, external links, schema files, or other non-Markdown resources as pages.
- Use `wiki_file_count` to discover wiki files that are not yet indexed, but do not overwrite the footer page count with `wiki_file_count` merely because the file scan is larger than the index coverage.
- If an existing wiki file is not in `index.md` and the task adds it for the first time, treat the change as `补录既有页面` / `first-time index backfill`, not as a newly created file. If the existing footer count matched the pre-change `indexed_page_count`, increment the footer page count by the number of newly indexed pages. If the existing footer count did not match the pre-change `indexed_page_count`, set the footer to the post-change `indexed_page_count` and record a `统计漂移修正` in `log.md`; do not blindly add to the stale footer number.
- If a task-scoped page already exists in `index.md` and the change only refreshes its summary, tags, section placement, path text, or maintenance wording, do not change the footer page-count number unless the footer differs from `indexed_page_count`.
- If a task creates a new wiki Markdown file and adds a new index entry for it, `wiki_file_count` and `indexed_page_count` should both increase; set the footer page count to the post-change `indexed_page_count` and record the count change in `log.md`.
- If a task deletes, migrates, renames, archives, de-indexes, or restores index coverage for wiki pages, update the footer page count from the post-change `indexed_page_count` and record whether this was an indexed-page addition, removal, rename/migration, de-index, or drift correction.
- If `wiki_file_count` is greater than `indexed_page_count`, report or repair task-scoped missing index entries according to the workflow. Do not automatically add every unindexed file unless the user asked for a full index rebuild, lint/audit repair, or broad index refresh.
- If `indexed_page_count` differs from the existing footer count, treat it as footer/statistics drift. Correct the footer count to `indexed_page_count` in the same edit and record the drift correction in `log.md`.
- Count domains from the vault schema or domain registry by default. If the operation adds, removes, or renames a registered domain, update the domain count and schema/index wording together.
- `.canvas` links may remain in `index.md` as explicit resource links, but they must not be included in the Markdown page count.
- After changing `index.md`, verify the post-change `indexed_page_count`, `wiki_file_count`, footer count, broken Markdown links, duplicate Markdown entries, and any task-scoped missing index entries. Explicitly recorded non-Markdown links are allowed.
- The `log.md` entry for any operation that changes `index.md` must state that the top update note and footer date were refreshed, list `wiki_file_count`, `indexed_page_count`, and footer count, and explicitly say whether the indexed page count changed, stayed unchanged, or was corrected because of statistics drift.

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
10. Run the Mandatory Maintenance Pass. If `index.md` changes, apply the Index Metadata And Statistics rules in the same edit. Then append `log.md` with `AGENTS.md`, `CLAUDE.md`, `index.md`, and frontmatter results plus any index metadata/statistics update result.
11. If a top-level raw/wiki directory is not registered in the schema, report it and ask before changing schema files.

### Query

Use when the user asks a question about the knowledge base.

1. Read `index.md` to locate candidate pages.
2. Read the most relevant wiki pages.
3. Synthesize the answer in Chinese and cite pages with `[[页面标题]]`.
4. Run the Mandatory Maintenance Pass for the pages and index/schema files touched by the query. If the user explicitly requested read-only or no file changes, report any maintenance gaps instead of writing them.
5. If the answer is worth preserving, suggest archiving it as a wiki page, but do not create one without user confirmation.

### Optimize Existing Wiki Pages

Use when the user asks to optimize, reorganize, add frontmatter, add summaries, or improve a specific wiki page.

1. Read the page and its declared `sources`.
2. Check whether YAML frontmatter exists and whether it contains all required note properties.
3. Preserve all existing image embeds and their order.
4. If the page contains image embeds or image-heavy sources, build an image manifest, resolve images from raw sources, and analyze coverage before writing.
5. If default agents are used, verify every manifest index has an analysis result or an explicit unresolved note before synthesis.
6. If the user says "不修改现有内容", "补充放最后", or otherwise requests append-only body changes, preserve the existing body and section order. Add new body material at the requested location, or at the end when the user asks for end-of-file additions.
7. Add or repair YAML frontmatter at the very top of the page as a structural maintenance exception, even during append-only body optimizations. This does not count as changing the existing body/order. Also repair inline tags, one-sentence summary, related links, and source citations when they are in scope.
8. Check whether the optimized page is already present in `index.md`. If it is already indexed, describe the index action as refreshing an existing page. If the file exists but is missing from `index.md`, describe the index action as `补录既有页面` / `first-time index backfill`; update the footer page count from `indexed_page_count`, not from `wiki_file_count`.
9. Add useful sections such as `资料总结`, `图片内容解析`, `洞见`, `方法论提炼`, `最佳实践`, `金句精选`, or quick-reference tables when they fit the material and the user's requested placement.
10. Run the Mandatory Maintenance Pass. If `index.md` changes, apply the Index Metadata And Statistics rules in the same edit. Then append `log.md` with `AGENTS.md`, `CLAUDE.md`, `index.md`, and frontmatter results plus any index metadata/statistics update result.

### Extract Thinking Frameworks

Use when the user asks to create or expand pages under `wiki/提炼思维/`.

1. Read all requested source wiki pages or directories.
2. Extract reusable patterns, mental models, workflows, best practices, pitfalls, and memorable lines.
3. Create or update a page under `wiki/提炼思维/` with no raw source layer unless the schema specifies one.
4. Link back to the source wiki pages and run the Mandatory Maintenance Pass. If `index.md` changes, apply the Index Metadata And Statistics rules in the same edit. Append `log.md` with `AGENTS.md`, `CLAUDE.md`, `index.md`, and frontmatter results plus any index metadata/statistics update result.

### Lint Or Audit

Use for health checks and maintenance.

Check for missing frontmatter, mismatched inline/frontmatter tags, broken wiki links, orphan pages, empty sources, unregistered raw/wiki directories, stale pages, duplicate index entries, and contradictions across related pages. Report findings first, then repair clear structural gaps by default unless the user explicitly asked for read-only/audit-only/no file changes.

Also run the Mandatory Maintenance Pass. For lint or audit tasks, repair clear structural gaps by default unless the user explicitly asked for read-only/audit-only/no file changes. If the lint or audit task changes `index.md`, apply the Index Metadata And Statistics rules in the same edit. If the lint or audit task changes files, append `log.md` with `AGENTS.md`, `CLAUDE.md`, `index.md`, and frontmatter results plus any index metadata/statistics update result.

### Index

Use when the user asks to rebuild or refresh `index.md`.

Scan `wiki/` markdown files, read frontmatter and summary lines, read current `index.md` entries, compute `wiki_file_count` and `indexed_page_count`, group pages by schema domains, preserve useful existing organization when possible, and apply the Index Metadata And Statistics rules whenever `index.md` changes.

When rebuilding or refreshing `index.md`, also check whether scanned paths reveal missing domain registrations or stale rules in `AGENTS.md` or `CLAUDE.md`.

Before finishing an index refresh, run the Mandatory Maintenance Pass for the requested index scope. Verify `wiki_file_count`, `indexed_page_count`, footer count, broken Markdown links, duplicate Markdown entries, missing index entries in scope, and any explicit non-Markdown links such as `.canvas`. Append a `log.md` entry if `index.md` changes, and state that the top update note and footer date were refreshed plus whether the indexed page count changed, stayed unchanged, or was corrected because of statistics drift.

### Migrate

Use for one-time migration of existing notes into the LLM Wiki structure.

Identify markdown files outside `raw/` and `wiki/`, ask for domain placement when not obvious, then move by explicit user-approved paths only. Avoid bulk operations. Preserve content, add frontmatter, update links, rebuild `index.md`, and append `log.md`.

Before and after migration, check `AGENTS.md`, `CLAUDE.md`, and `index.md` for path, domain, and summary freshness. If `index.md` changes, apply the Index Metadata And Statistics rules in the same edit. Record all three results and any index metadata/statistics update result in `log.md` when files are changed.

### Delete Or Remove Wiki Pages

Use only when the user explicitly asks to delete, remove, archive, or de-index wiki content.

1. Never delete anything under `raw/`.
2. Prefer archiving or de-indexing over deletion unless the user clearly asks for physical deletion.
3. If a wiki file must be deleted, delete only one explicit file path at a time with the safe Windows deletion rule above.
4. Check whether related links, backlinks, `index.md`, `AGENTS.md`, or `CLAUDE.md` need updates after the removal.
5. If `index.md` changes, apply the Index Metadata And Statistics rules in the same edit. Append `log.md` with the deletion/removal action, the freshness result for `AGENTS.md`, `CLAUDE.md`, and `index.md`, and any index metadata/statistics update result.

## Page Requirements

Every wiki page should contain:

1. YAML frontmatter as the first line/block of the file, starting with `---`, with `title`, `created`, `updated`, `domain`, `tags`, `sources`, and `status`.
2. Inline tags matching frontmatter tags when inline tags are used.
3. Tags normalized so spaces inside tag segments become `_`, such as `domain/AI_Live`.
4. A one-sentence summary in blockquote form.
5. Main content.
6. `## 相关` with meaningful wiki links.
7. `## 来源` pointing to raw directories or files, except schema-defined no-raw domains such as extracted thinking pages.

Use the current date from the environment for `created`, `updated`, and log entries.
