#!/usr/bin/env python3
"""分阶段合并 defer 队列；仅标准库，不编辑 index，不删除任何文件。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid
from datetime import date

TASKS = {'enhance-wiki-content', 'optimize', 'update-raw-reference', 'ingest', 'delete'}
MARKER = '<!-- obsidian-llm-wiki queue v1 -->'
BASE = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inside(root, path):
    for part in (path, *path.parents):
        if part == root.parent:
            break
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise ValueError('symlink/junction not allowed in queue workflow paths')
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError('path escapes allowed root')
    return resolved


def safe_file(root, path):
    resolved = inside(root, path)
    if not resolved.is_file():
        raise ValueError('expected regular file: ' + path.name)
    return resolved


def log_entry(text):
    text = text.replace('\r\n', '\n').strip('\n')
    headings = re.findall(r'^## \[(\d{4}-\d{2}-\d{2})\] .+$', text, re.M)
    if len(headings) != 1 or not text.startswith('## ['):
        raise ValueError('exactly one leading log heading required')
    date.fromisoformat(headings[0])
    for key in ('范围', '变更', '维护', '验证'):
        if not re.search(r'^- ' + key + r'[:：].+', text, re.M):
            raise ValueError('missing log field: ' + key)
    return text + '\n'


def fragment(vault, path):
    safe_file(vault / 'logs' / 'queue', path)
    raw = path.read_bytes()
    text = raw.decode('utf-8-sig').replace('\r\n', '\n')
    if text.count(MARKER) != 1:
        raise ValueError('invalid queue marker')
    meta = {}
    for key in ('task', 'date', 'page', 'section', 'summary'):
        values = re.findall(r'^<!-- ' + key + r': (.*?) -->$', text, re.M)
        if len(values) != 1 or not values[0].strip():
            raise ValueError('missing or duplicate metadata: ' + key)
        meta[key] = values[0].strip()
    if meta['task'] not in TASKS:
        raise ValueError('unsupported task')
    date.fromisoformat(meta['date'])
    page = meta['page'].replace('\\', '/')
    if not page.startswith('wiki/') or '..' in Path(page).parts or Path(page).suffix != '.md':
        raise ValueError('invalid wiki page path')
    target = inside(vault / 'wiki', vault / page)
    if meta['task'] != 'delete' and not target.is_file():
        raise ValueError('missing page; retain fragment')
    if target.exists() and not target.is_file():
        raise ValueError('page is not a file')
    meta['page'] = page
    for name in ('index', 'log'):
        begin, end = '<!-- ' + name + '-entry -->', '<!-- /' + name + '-entry -->'
        if text.count(begin) != 1 or text.count(end) != 1 or text.index(begin) > text.index(end):
            raise ValueError('invalid entry fences')
        meta[name] = text.split(begin)[1].split(end)[0].strip('\n')
    if meta['task'] != 'delete' and not re.fullmatch(r'\|\s*\[\[.+?\]\]\s*\|[^\n]+\|', meta['index']):
        raise ValueError('index table row required')
    meta['log'] = log_entry(meta['log'])
    if not meta['log'].startswith('## [' + meta['date'] + '] '):
        raise ValueError('log date mismatch')
    meta.update(file=path.name, sha256=digest(raw), page_sha256=digest(target.read_bytes()) if target.is_file() else None)
    return meta


def inspect(vault):
    queue = inside(vault, vault / 'logs' / 'queue')
    valid, invalid = [], []
    if queue.exists():
        for path in sorted(queue.glob('*.md')):
            try:
                valid.append(fragment(vault, path))
            except (ValueError, OSError, UnicodeError) as exc:
                invalid.append({'file': path.name, 'error': str(exc)})
    conflicts = {f['page'] for f in valid if sum(g['page'].casefold() == f['page'].casefold() for g in valid) > 1}
    for f in valid:
        if f['page'] in conflicts:
            invalid.append({'file': f['file'], 'error': 'same-page conflict; retain all'})
    return [f for f in valid if f['page'] not in conflicts], invalid


def pending_entries(existing, entries):
    """仅完整条目相同才去重；同标题不同内容及部分写入均停止。"""
    normalized = existing.decode('utf-8-sig').replace('\r\n', '\n')
    blocks = re.split(r'(?=^## \[)', normalized, flags=re.M)
    by_title = {}
    for block in blocks:
        if block.startswith('## ['):
            by_title.setdefault(block.splitlines()[0], []).append(block.rstrip('\n'))
    pending = []
    for entry in entries:
        title = entry.splitlines()[0]
        found = by_title.get(title, [])
        if found:
            if found != [entry.rstrip('\n')]:
                raise ValueError('log title/content conflict: ' + title)
        else:
            pending.append(entry)
            by_title[title] = [entry.rstrip('\n')]
    newline = '\r\n' if b'\r\n' in existing else '\n'
    text = ''.join('\n' + entry for entry in pending)
    if existing and not existing.endswith(b'\n') and pending:
        text = '\n' + text
    return text.replace('\n', newline).encode('utf-8')


def validator():
    spec = importlib.util.spec_from_file_location('queue_index_stat', BASE / 'references' / 'index_stat.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_index(vault, selected):
    stat = validator()
    result = stat.build_payload(vault)
    if not result['footer_match']:
        raise ValueError('index footer mismatch')
    index_text = (vault / 'index.md').read_text(encoding='utf-8-sig')
    dates = re.findall(r'^> 由 LLM 维护。上次更新：(\d{4}-\d{2}-\d{2})', index_text, re.M)
    footers = stat.FOOTER_STAT.findall(index_text)
    if len(dates) != 1 or len(footers) != 1 or len(stat.FOOTER_HEALTH.findall(index_text)) != 1 or dates[0] != footers[0][-1]:
        raise ValueError('index metadata/footer must be unique and dates must match')
    pages = stat.scan_wiki(vault)
    candidates = sorted(set(pages + [f['page'] for f in selected]))
    targets = stat.extract_index_targets(vault)
    resolved = [stat.resolve_target(t, candidates)[0] for t in targets]
    for f in selected:
        count = resolved.count(f['page'])
        if count != (0 if f['task'] == 'delete' else 1):
            raise ValueError('index action not complete: ' + f['file'])
    return result


def save(lock, state):
    # 已持锁状态；崩溃产生的非法 JSON 必须人工检查，绝不视为空闲锁。
    safe_file(lock.parent, lock)
    with lock.open('wb') as stream:
        stream.write(json.dumps(state, ensure_ascii=False, indent=2).encode('utf-8'))
        stream.flush()
        os.fsync(stream.fileno())


def owned(lock, token):
    safe_file(lock.parent, lock)
    state = json.loads(lock.read_text(encoding='utf-8'))
    if not token or state['token'] != token:
        raise ValueError('lock owner token mismatch')
    return state


def unchanged(vault, selected):
    for f in selected:
        current = fragment(vault, vault / 'logs' / 'queue' / f['file'])
        if current != f:
            raise ValueError('snapshot changed: ' + f['file'])


def validate_payload(current, state):
    size = state['before_size']
    prefix_ok = len(current) >= size and digest(current[:size]) == state['before_sha']
    payload = state['payload'].encode('utf-8')
    return prefix_ok and current[size:] == payload, prefix_ok and len(current) == size


def execute(args):
    vault = Path(args.vault_root).resolve()
    if not vault.is_dir() or not (vault / 'wiki').is_dir():
        raise ValueError('initialized vault required')
    for name in ('index.md', 'log.md'):
        safe_file(vault, vault / name)
    queue = inside(vault, vault / 'logs' / 'queue')
    lock = queue / '.sync.lock'
    inside(queue, lock)
    if args.dry_run:
        valid, invalid = inspect(vault)
        return {'status': 'dry_run', 'valid': valid, 'invalid': invalid, 'lock_present': lock.exists(), 'writes': 0}
    if args.phase == 'acquire':
        queue.mkdir(parents=True, exist_ok=True)
        state = {'token': uuid.uuid4().hex, 'pid': os.getpid(), 'created': time.time(), 'phase': 'acquired'}
        try:
            with lock.open('xb') as stream:
                stream.write(json.dumps(state).encode('utf-8'))
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            raise ValueError('lock exists; age alone does not authorize removal')
        state['snapshot'], state['invalid'] = inspect(vault)
        save(lock, state)
        return state
    state = owned(lock, args.token)
    if args.phase == 'prepare':
        if state['phase'] not in ('acquired', 'prepared'):
            raise ValueError('cannot reprepare after append began')
        names = args.include or []
        if len(names) != len(set(names)):
            raise ValueError('duplicate include')
        selected = [f for f in state['snapshot'] if f['file'] in names]
        if len(selected) != len(names):
            raise ValueError('include must name valid snapshot fragments')
        unchanged(vault, selected)
        check_index(vault, selected)
        if not args.sync_entry:
            raise ValueError('--sync-entry required')
        entry_path = safe_file(vault, Path(args.sync_entry).resolve())
        final = log_entry(entry_path.read_text(encoding='utf-8'))
        if not re.match(r'^## \[.*?\] sync \|', final):
            raise ValueError('sync final heading required')
        existing = (vault / 'log.md').read_bytes()
        entries = [f['log'] for f in selected] + [final]
        # 历史分卷也参与完整条目去重，防止轮转后重跑重复追加。
        history = existing
        archive = inside(vault, vault / 'logs' / 'archive')
        if archive.exists():
            for path in sorted(archive.glob('*.md')):
                history += b'\n' + safe_file(archive, path).read_bytes()
        filtered = pending_entries(history, entries).decode('utf-8').replace('\r\n', '\n')
        chunks = re.findall(r'^## \[.*?(?=^## \[|\Z)', filtered, re.M | re.S)
        payload = pending_entries(existing, [log_entry(c) for c in chunks])
        pending_titles = {c.splitlines()[0] for c in chunks}
        skipped = [f['file'] for f in selected if f['log'].splitlines()[0] not in pending_titles]
        state.update(phase='prepared', selected=selected, payload=payload.decode('utf-8'),
                     skipped_duplicate=skipped,
                     before_sha=digest(existing), before_size=len(existing),
                     index_sha=digest((vault / 'index.md').read_bytes()))
        save(lock, state)
        return {'status': 'prepared', 'append_bytes': len(payload), 'token': state['token'],
                'skipped_duplicate': skipped}
    if args.phase in ('append', 'verify'):
        if state['phase'] not in ('prepared', 'appending', 'appended'):
            raise ValueError('prepare required')
        unchanged(vault, state['selected'])
        stats = check_index(vault, state['selected'])
        if digest((vault / 'index.md').read_bytes()) != state['index_sha']:
            raise ValueError('index changed since prepare')
        path = vault / 'log.md'
        current = path.read_bytes()
        payload = state['payload'].encode('utf-8')
        size = state['before_size']
        complete, untouched = validate_payload(current, state)
        if not complete:
            if args.phase == 'verify' or not untouched or state['phase'] == 'appended':
                raise ValueError('partial append or external log change; retain all files')
            # PendingPlanFile 从持锁计划中读取确切 payload，避免长命令参数截断。
            command = ['powershell.exe', '-NoProfile', '-File', str(BASE / 'scripts' / 'log-preflight.ps1'),
                       '-VaultRoot', str(vault), '-PendingPlanFile', str(lock), '-Json']
            preflight = json.loads(subprocess.run(command, check=True, capture_output=True, encoding='utf-8').stdout)
            if preflight['rotation_due']:
                return {'status': 'rotation_required', 'preflight': preflight, 'retained': True}
            state['phase'] = 'appending'
            save(lock, state)
            with path.open('r+b') as stream:
                data = stream.read()
                if len(data) != size or digest(data) != state['before_sha']:
                    raise ValueError('log changed before append')
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            current = path.read_bytes()
            if digest(current[:size]) != state['before_sha'] or current[size:] != payload or not current.endswith(b'\n'):
                raise ValueError('append verification failed')
        if not current.endswith(b'\n'):
            raise ValueError('final newline missing')
        state['phase'] = 'appended'
        save(lock, state)
        return {'status': 'verified', 'prefix_sha256_unchanged': True, 'stats': stats,
                'merged': [f['file'] for f in state['selected'] if f['file'] not in state['skipped_duplicate']],
                'skipped_duplicate': state['skipped_duplicate'], 'retained_invalid': state['invalid'],
                'cleanup': [str(queue / f['file']) for f in state['selected']],
                'lock_cleanup_last': str(lock), 'automatic_deletions': 0}
    raise ValueError('--phase required for writes')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vault-root', required=True)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--phase', choices=('acquire', 'prepare', 'append', 'verify'))
    parser.add_argument('--token')
    parser.add_argument('--include', action='append')
    parser.add_argument('--sync-entry')
    args = parser.parse_args()
    if args.dry_run and any((args.phase, args.token, args.include, args.sync_entry)):
        parser.error('--dry-run cannot be combined with write-phase arguments')
    try:
        result = execute(args)
        print(json.dumps(result, ensure_ascii=True, indent=2))
    except (ValueError, OSError, UnicodeError, subprocess.SubprocessError) as exc:
        print(json.dumps({'status': 'blocked', 'error': str(exc)}, ensure_ascii=True))
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
