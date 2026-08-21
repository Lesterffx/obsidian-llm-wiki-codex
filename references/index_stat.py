#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate the six index statistics used by obsidian-llm-wiki.

Usage:
    python index_stat.py <vault_root> [--json]

The script is read-only and uses only the Python standard library. It reports:
indexed_page_count, wiki_file_count, registered_domain_count, missing_count,
broken_count, duplicate_count, issue details, and footer drift.

Exit codes:
    0: scan completed, including scans that found health issues or drift
    2: invalid arguments or vault structure
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Optional


for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")


ATTACHMENT_EXTENSIONS = {
    ".canvas",
    ".excalidraw",
    ".gif",
    ".jpeg",
    ".jpg",
    ".mdx",
    ".mov",
    ".mp3",
    ".mp4",
    ".pdf",
    ".png",
    ".svg",
    ".webp",
    ".wav",
}
EXCLUDED_PAGE_NAMES = {"index.md", "log.md"}
EXCLUDED_DIRECTORY_NAMES = {"assets", "templates"}
EXAMPLE_TARGETS = {"页面标题"}

INDEX_ROW = re.compile(r"^\|\s*\[\[([^\]]+)\]\]\s*\|")
FOOTER_STAT = re.compile(
    r"_统计：(\d+) 个已索引页面 \| (\d+) 个 Wiki 文件 \| (\d+) 个注册领域 "
    r"\| 上次更新于 (\d{4}-\d{2}-\d{2})_"
)
FOOTER_HEALTH = re.compile(
    r"> 索引健康：未收录 (\d+) \| Markdown 断链 (\d+) \| 重复条目 (\d+)"
)


def read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def scan_wiki(vault: Path) -> list[str]:
    """Return page paths relative to the vault, using POSIX separators."""
    wiki_root = vault / "wiki"
    if not wiki_root.is_dir():
        return []

    pages: list[str] = []
    for path in wiki_root.rglob("*.md"):
        if not path.is_file() or path.name.lower() in EXCLUDED_PAGE_NAMES:
            continue
        relative = path.relative_to(vault)
        if any(part.lower() in EXCLUDED_DIRECTORY_NAMES for part in relative.parts[:-1]):
            continue
        pages.append(relative.as_posix())
    return sorted(pages)


def count_domain_rows(schema_path: Path) -> Optional[int]:
    """Count data rows in the first table following a domain-registry heading."""
    text = read_utf8(schema_path)
    heading = re.search(r"^#{1,3}\s*.*领域注册表.*$", text, flags=re.MULTILINE)
    if not heading:
        return None

    table_lines: list[str] = []
    for line in text[heading.end() :].splitlines():
        stripped = line.strip()
        if stripped.startswith("|"):
            table_lines.append(stripped)
        elif table_lines:
            break

    if len(table_lines) < 2:
        return None

    data_rows = [
        line
        for line in table_lines[1:]
        if not re.fullmatch(r"\|[\s:|-]+\|?", line)
    ]
    return len(data_rows)


def count_registered_domains(vault: Path) -> tuple[Optional[int], list[str]]:
    """Prefer AGENTS.md for Codex and compare CLAUDE.md when both exist."""
    agents_path = vault / "AGENTS.md"
    claude_path = vault / "CLAUDE.md"
    agents_count = count_domain_rows(agents_path) if agents_path.is_file() else None
    claude_count = count_domain_rows(claude_path) if claude_path.is_file() else None
    notes: list[str] = []

    if agents_path.is_file() and agents_count is None:
        notes.append("AGENTS.md: 未找到『领域注册表』表格")
    if claude_path.is_file() and claude_count is None:
        notes.append("CLAUDE.md: 未找到『领域注册表』表格")

    if agents_count is not None:
        if claude_count is not None and claude_count != agents_count:
            notes.append(
                "双入口注册表行数不一致："
                f"AGENTS.md={agents_count}, CLAUDE.md={claude_count}（须先同步再计数）"
            )
        return agents_count, notes

    if claude_count is not None:
        notes.append(f"registered_domain_count 回退取自 CLAUDE.md（{claude_count}）")
        return claude_count, notes

    if not agents_path.is_file() and not claude_path.is_file():
        notes.append("vault 根未找到 AGENTS.md 或 CLAUDE.md")
    return None, notes


def extract_index_targets(vault: Path) -> list[str]:
    """Extract only page links in Markdown table data rows, outside code fences."""
    targets: list[str] = []
    in_fence = False
    fence_marker = ""

    for line in read_utf8(vault / "index.md").splitlines():
        stripped = line.lstrip()
        fence = re.match(r"(```+|~~~+)", stripped)
        if fence:
            marker = fence.group(1)[0]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            continue
        if in_fence:
            continue

        match = INDEX_ROW.match(line)
        if not match:
            continue
        target = match.group(1).split("|", 1)[0].split("#", 1)[0].strip()
        if target:
            targets.append(target)
    return targets


def is_excluded_target(target: str) -> bool:
    normalized = target.replace("\\", "/").strip()
    lowered = normalized.lower()
    if normalized in EXAMPLE_TARGETS:
        return True
    if lowered.startswith(("raw/", "http://", "https://", "mailto:")):
        return True
    return PurePosixPath(lowered).suffix in ATTACHMENT_EXTENSIONS


def resolve_target(target: str, wiki_files: list[str]) -> tuple[Optional[str], Optional[str]]:
    """Resolve a title or wiki-relative path to exactly one Markdown page."""
    normalized = target.replace("\\", "/").strip().lstrip("/")
    if normalized.startswith("wiki/"):
        normalized = normalized[5:]

    path_candidates: set[str] = set()
    if "/" in normalized or normalized.lower().endswith(".md"):
        relative = normalized if normalized.lower().endswith(".md") else normalized + ".md"
        candidate = "wiki/" + relative
        if candidate in wiki_files:
            path_candidates.add(candidate)

    title = PurePosixPath(normalized).stem if normalized.lower().endswith(".md") else PurePosixPath(normalized).name
    stem_candidates = {page for page in wiki_files if PurePosixPath(page).stem == title}
    candidates = path_candidates or stem_candidates

    if len(candidates) == 1:
        return next(iter(candidates)), None
    if len(candidates) > 1:
        return None, "歧义: " + " | ".join(sorted(candidates))
    return None, "未命中"


def resolve_targets(
    targets: list[str], wiki_files: list[str]
) -> tuple[set[str], list[dict[str, str]], Counter[str]]:
    resolved: set[str] = set()
    broken: list[dict[str, str]] = []
    seen: Counter[str] = Counter()

    for target in targets:
        if is_excluded_target(target):
            continue
        page, reason = resolve_target(target, wiki_files)
        if page is None:
            broken.append({"target": target, "reason": reason or "未命中"})
            continue
        seen[page] += 1
        resolved.add(page)
    return resolved, broken, seen


def read_footer(vault: Path) -> Optional[dict[str, int]]:
    text = read_utf8(vault / "index.md")
    stat_match = FOOTER_STAT.search(text)
    health_match = FOOTER_HEALTH.search(text)
    if not stat_match or not health_match:
        return None
    return {
        "indexed_page_count": int(stat_match.group(1)),
        "wiki_file_count": int(stat_match.group(2)),
        "registered_domain_count": int(stat_match.group(3)),
        "missing_count": int(health_match.group(1)),
        "broken_count": int(health_match.group(2)),
        "duplicate_count": int(health_match.group(3)),
    }


def build_payload(vault: Path) -> dict[str, object]:
    wiki_files = scan_wiki(vault)
    domain_count, domain_notes = count_registered_domains(vault)
    targets = extract_index_targets(vault)
    resolved, broken, seen = resolve_targets(targets, wiki_files)

    missing = [page for page in wiki_files if page not in resolved]
    duplicates = {page: count for page, count in sorted(seen.items()) if count > 1}
    result: dict[str, Optional[int]] = {
        "indexed_page_count": len(resolved),
        "wiki_file_count": len(wiki_files),
        "registered_domain_count": domain_count,
        "missing_count": len(missing),
        "broken_count": len(broken),
        "duplicate_count": sum(count - 1 for count in duplicates.values()),
    }

    footer = read_footer(vault)
    drift = None
    if footer is not None:
        drift = {
            key: {"footer": footer[key], "scan": value}
            for key, value in result.items()
            if footer[key] != value
        }

    return {
        "vault": str(vault),
        **result,
        "missing": missing,
        "broken": broken,
        "duplicates": duplicates,
        "domain_notes": domain_notes,
        "footer": footer,
        "footer_match": footer is not None and not drift,
        "drift": drift,
    }


def print_human(payload: dict[str, object]) -> None:
    keys = (
        "wiki_file_count",
        "indexed_page_count",
        "registered_domain_count",
        "missing_count",
        "broken_count",
        "duplicate_count",
    )
    print("== obsidian-llm-wiki index 六变量精校 ==")
    print(f"vault: {payload['vault']}")
    for key in keys:
        print(f"{key + ':':26}{payload[key]}")

    for path in payload["missing"]:
        print(f"  MISSING: {path}")
    for item in payload["broken"]:
        print(f"  BROKEN:  {item['target']} ({item['reason']})")
    for path, count in payload["duplicates"].items():
        print(f"  DUP:     {path} ×{count}")
    for note in payload["domain_notes"]:
        print(f"  NOTE:    {note}")

    if payload["footer"] is None:
        print("页脚对照: 未找到统计行或索引健康行")
    elif payload["footer_match"]:
        print("页脚对照: 一致（footer_match=true）")
    else:
        print("页脚对照: 漂移（footer_match=false；明细见 --json）")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="obsidian-llm-wiki index 六变量精校")
    parser.add_argument("vault_root", help="vault 根目录（包含 index.md 与 wiki/）")
    parser.add_argument("--json", action="store_true", help="输出 UTF-8 JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    vault = Path(args.vault_root).expanduser().resolve()
    if not vault.is_dir():
        print(f"错误：vault 根不存在：{vault}", file=sys.stderr)
        return 2
    if not (vault / "index.md").is_file():
        print(f"错误：index.md 不存在：{vault / 'index.md'}", file=sys.stderr)
        return 2
    if not (vault / "wiki").is_dir():
        print(f"错误：wiki 目录不存在：{vault / 'wiki'}", file=sys.stderr)
        return 2

    payload = build_payload(vault)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_human(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
