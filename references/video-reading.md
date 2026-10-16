# Video Reading In Codex

Read this reference for in-scope videos during `ingest`, `optimize`, or the two-path `enhance-wiki-content` form. These are Skill workflows, not shell executables. This reference adds visual video evidence; it does not widen any command's source, metadata, body, index, or defer permissions.

## Options And Routing

- Video reading is on by default for these three workflows. Accept `--no-video` and `--defer` in either order after the command name and before positional paths. Reject unknown, repeated, or misplaced options and invalid path counts before any writes or preprocessing. Do not treat options as paths.
- `--no-video` skips video capability probes, ffprobe, hashing video contents, extraction, video visual tools, and attached-subtitle discovery/reading. Inventory existing video references for preservation, with `skipped (--no-video)` status. Existing page prose remains usable. Do not run the helper merely to document a skip.
- The one-path `enhance-wiki-content` form is always prose-only, with or without flags: no raw media or subtitle discovery, no video probes, and no temporary artifacts. Preserve its narrow missing-field/sparse-tag/index rules.
- `--defer` changes only shared-file finalization. Reading and page-level verification still finish; write channel/coverage results into the private queue log entry instead of changing index/schema/log files. Queue v1 and helper interfaces remain unchanged.
- `query-image`, `update-raw-reference`, `sync`, and other commands gain no video-reading behavior or `--no-video` option.

```text
$obsidian-llm-wiki ingest "raw/<domain>/<material>/"
$obsidian-llm-wiki optimize --no-video "wiki/<domain>/<page>.md"
$obsidian-llm-wiki enhance-wiki-content --defer --no-video "wiki/<domain>/<page>.md" "raw/<domain>/<material>/"
```

## Ordered Media Manifest

Extend the existing in-memory image manifest; do not create a separate ordering system or rewrite references. Recognize videos case-insensitively: `mp4/mov/webm/m4v/mkv/avi/ogv`. Audio references remain inventory-only; do not play or transcribe audio.

Include actual Obsidian media embeds and local inline Markdown video attachment links pointing into raw, including `[clip](<../../raw/.../clip.mp4>)`. Exclude frontmatter, code, escaped syntax and comments. Parse Markdown before decoding its local destination once; never decode Obsidian filenames. Do not follow remote URLs, HTML, reference definitions or unsupported syntax. Relative Markdown links resolve from the page directory; explicit vault-relative `raw/...` targets resolve from the vault root.

For each source position record: stable index, original expression and syntax, media type, actual path, declared-source match, size, duration when probed, channel, coverage and reading status. Keep repeated references as separate positions; reuse analysis only after unique file identity is confirmed. Frame indexes belong to their parent video index, never replace source positions. Keep reference count, unique videos and sampled frames separate.

Apply the invoking command's existing real-path boundaries, including junctions/symlinks. Two-path enhancement confines reading to the supplied raw directory; never redirect an explicit reference to another source or read out-of-scope files. File-scoped sources do not authorize sibling files. Preserve missing/ambiguous/out-of-scope references and report them without guessing. In raw-only directories, use natural filename order. Reconcile in-scope unreferenced videos without inserting new embeds. A non-embedded attachment is still source evidence, not a request to convert its syntax.

## Capability And Local Sampling

1. Inventory the video before making any capability claim. Inspect tools actually exposed by this Codex runtime; ZCode's `Read`, tool identifiers, credentials and successful runs are not Codex capabilities.
2. If an authorized native video tool is actually exposed, probe a small representative in-scope video. Success requires returned visual frames or actual visual interpretation with traceable times; a filename, metadata, URL or upload receipt is insufficient. Reuse the probe evidence. Apply actual tool limits; never copy an unverified size limit from another runtime.
3. Otherwise, or for an individual video that exceeds that tool's limits, use existing local ffprobe/ffmpeg with the fixed helper below. Confirm vision on one generated frame with the runtime's actual image viewer (for example `view_image`). If image vision fails, do not generate/read every remaining video or dispatch futile batches. Retain the inventory and mark visual coverage unavailable.
4. Use only an already configured and authorized visual MCP when needed. Do not install a service, add credentials, upload to a new destination, or try another runtime's gateway. Local extraction does not mean local inference: frames read by the model use the current model service and its existing data-transfer permissions.

Run with the existing project interpreter under the Skill's Windows/Python priority order. All paths are explicit arguments; no shell substitution or source-text commands:

```powershell
& ".\.venv\Scripts\python.exe" -X utf8 -B "<skill_base>\scripts\preprocess_video.py" `
  --input "<absolute-raw-video>" `
  --vault-root "<absolute-vault-root>" `
  --source-scope "<confirmed-raw-directory-or-file>" `
  --task-id "<unique-safe-task-id>"
```

The helper uses only the Python standard library and existing `ffprobe`/`ffmpeg` executables. It installs nothing, changes no PATH and restricts media protocols to local files. Documentation for the underlying tools: [ffprobe](https://ffmpeg.org/ffprobe.html), [ffmpeg](https://ffmpeg.org/ffmpeg.html).

- Validate all workflow arguments and safe frontmatter **before** preprocessing. An invalid enhancement must not create even temporary files.
- Use one fresh task id per unique video. The helper refuses an existing task directory and checks real containment in the vault's raw and supplied source scope. It never reads a URL or edits raw/wiki/index/log/schema files.
- Default sampling targets every 5 seconds plus the final segment, with at most 60 frames per video. Long videos widen the interval evenly across the timeline. Preserve aspect ratio with a maximum width of 1600 pixels; disclose unreadable small text rather than infer it.
- `video-manifest.json` records source SHA-256, size/duration, requested sample times, decoded source PTS and relative timeline times when available, individual decode failures, subtitle candidates and source-hash verification. An unknown actual timestamp stays null; never report frame numbers or requested seek times as observed timestamps.
- Read every successful frame in manifest order or explicitly mark an unread position. Attribute observations to the parent video and available time. Video count is not image count; preserve existing image batching and delegation permission rules. The main agent reads video frames unless delegation is explicitly authorized.
- Sampling can miss brief transitions, speech, or details between frames. Say `抽样画面分析`, state the interval/frame count and limitations, and never claim full playback, precise transcription or complete coverage.
- A missing tool, corrupt clip or unsupported stream affects that video only. Continue other verified evidence; do not keep retrying the same failure. No usable evidence means no content write. A changed source hash invalidates that video's evidence and must be reported.

## Existing Subtitles

Visible subtitles are visual evidence. Separately identify page prose and existing subtitle-file evidence; do not present either as something heard in the recording.

The helper reports same-stem `.srt`/`.vtt` candidates in the video's directory only when their real paths stay inside raw and the confirmed source scope. One candidate is available; multiple candidates are ambiguous and are not chosen automatically. Other explicitly referenced SRT/VTT files may be read only after the agent verifies scope and association. Read subtitle text as UTF-8 (BOM allowed); report unsupported encoding instead of guessing. File-scoped video input alone does not authorize sibling subtitles. A damaged video may still have independently verified subtitle evidence, but that is not visual success.

Do not recursively search other directories, extract speech, run ASR, or treat a model's video response as an audio transcript. `--no-video` also skips this subtitle-file branch.

## Preservation, Cleanup And Finalization

Video observations may inform the same authorized synthesis sections as images. Two-path enhancement still appends at EOF, retains all old body bytes/standalone-tag exceptions, metadata restrictions, media suffixes/count/order and no-new-embed rules. New sparse tags may use verified in-scope visual/subtitle evidence; one-path tags still use this page's prose only.

Keep all generated outputs under `<vault>/tmp/obsidian-llm-wiki/<task-id>/`. The helper maintains `created_files.json` for both successful and controlled-failure decoding. It never deletes anything. Follow [temp-cleanup.md](temp-cleanup.md): freeze the exact cleanup list, verify and delete one registered literal-path file at a time, then registered empty directories deepest-first; retain protected `tmp/` and other workflows. Never use automatic recursive cleanup or delete a source. Report controlled residuals.

Before the final ordinary log entry or deferred queue fragment, record channel/probe outcome, videos sampled/skipped/unresolved, frame coverage, subtitle evidence, source-hash result and cleanup state. No-op and read-only workflows retain their original no-write rules. Do not persist a capability claim or edit vault schema merely because a video was inspected.

Public releases contain only generic instructions, helper code and synthetic test source. Never commit videos, subtitles, extracted frames, real names/paths, source hashes, private manifests, cleanup lists, logs or test-run directories.
