"""显式选择空沙箱路径的集成验证。仅创建虚构资料，不自动删除；输出逐文件清理清单。"""
import argparse
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('exercise_queue', BASE / 'scripts/flush_queue.py')
queue = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(queue)


def run(root):
    if root.exists():
        raise ValueError('sandbox must not already exist')
    created = []
    def put(name, text):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode('utf-8'))
        if str(path) not in created:
            created.append(str(path))
        return path
    def entry(title):
        return '## [2026-09-13] ' + title + '\n\n- 范围：示例。\n- 变更：示例。\n- 维护：检查。\n- 验证：通过。\n'
    def fragment(name, page='example', task='ingest'):
        row = '' if task == 'delete' else '| [[example]] | 示例 | 标签 |'
        return put('logs/queue/' + name, '\n'.join([
            queue.MARKER, '<!-- task: ' + task + ' -->', '<!-- date: 2026-09-13 -->',
            '<!-- page: wiki/' + page + '.md -->', '<!-- section: ## Example -->',
            '<!-- summary: example -->', '<!-- index-entry -->', row,
            '<!-- /index-entry -->', '<!-- log-entry -->', entry(task + ' | ' + name), '<!-- /log-entry -->\n']))
    def args(phase=None, token=None, includes=None, dry=False):
        return argparse.Namespace(vault_root=str(root), dry_run=dry, phase=phase, token=token,
                                  include=includes, sync_entry=str(root / 'sync-entry.md'))
    def blocked(call):
        try:
            call()
        except ValueError:
            return
        raise AssertionError('expected blocked action')
    put('wiki/example.md', '---\ntitle: example\n---\n示例正文\n')
    put('AGENTS.md', '# Schema\n\n## 领域注册表\n\n| 领域 | raw | wiki | 描述 |\n|---|---|---|---|\n| Example | raw/ | wiki/ | Example |\n')
    put('index.md', '# Index\n\n> 由 LLM 维护。上次更新：2026-09-13（示例）。\n\n## Example\n\n| 页面 | 摘要 | 标签 |\n|---|---|---|\n| [[example]] | 示例 | 标签 |\n\n_统计：1 个已索引页面 | 1 个 Wiki 文件 | 1 个注册领域 | 上次更新于 2026-09-13_\n\n> 索引健康：未收录 0 | Markdown 断链 0 | 重复条目 0；示例。\n')
    original = b'# Log\r\n'
    put('log.md', original.decode())
    put('sync-entry.md', entry('sync | synthetic-batch'))
    fragment('001-ingest.md')
    fragment('002-delete.md', page='removed', task='delete')
    before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
    report = queue.execute(args(dry=True))
    assert len(report['valid']) == 2
    assert before == {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
    state = queue.execute(args('acquire'))
    token = state['token']
    created.append(str(root / 'logs/queue/.sync.lock'))
    blocked(lambda: queue.execute(args('acquire')))
    fragment('003-later.md', page='later')
    put('wiki/later.md', 'later')
    # 新投放保持下一轮，模拟实际文件数与统计随扫描更新。
    index = (root / 'index.md').read_text(encoding='utf-8').replace('1 个 Wiki 文件', '2 个 Wiki 文件').replace('未收录 0', '未收录 1')
    put('index.md', index)
    selected = ['001-ingest.md', '002-delete.md']
    queue.execute(args('prepare', token, selected))
    with patch.object(queue.subprocess, 'run') as preflight:
        preflight.return_value.stdout = '{"rotation_due":true}'
        assert queue.execute(args('append', token))['status'] == 'rotation_required'
    assert (root / 'log.md').read_bytes() == original
    # 模拟整卷轮转后的新活动卷，旧日志字节原样归档。
    put('logs/archive/log-example.md', original.decode())
    put('log.md', '# Active\r\n')
    original = (root / 'log.md').read_bytes()
    queue.execute(args('prepare', token, selected))
    prepared = json.loads((root / 'logs/queue/.sync.lock').read_text(encoding='utf-8'))
    put('log.md', (original + prepared['payload'].encode()[:30]).decode('utf-8'))
    blocked(lambda: queue.execute(args('append', token)))
    put('log.md', original.decode())
    # 实际调用 PowerShell 预检与二进制追加。
    result = queue.execute(args('append', token))
    assert result['status'] == 'verified' and len(result['cleanup']) == 2
    after = (root / 'log.md').read_bytes()
    assert after.startswith(original) and after.endswith(b'\r\n')
    assert after.decode().index('001-ingest') < after.decode().index('002-delete') < after.decode().index('sync |')
    assert queue.execute(args('append', token))['status'] == 'verified'
    assert (root / 'log.md').read_bytes() == after
    assert queue.execute(args('verify', token))['automatic_deletions'] == 0
    assert (root / 'logs/queue/003-later.md').exists()
    # verify 之后仍不删除；清理需要外部逐文件执行。
    manifest = root / 'created_files.json'
    created.append(str(manifest))
    directories = sorted({str(root), *(str(parent) for p in map(Path, created) for parent in p.parents if parent.is_relative_to(root))}, key=lambda p: len(Path(p).parts), reverse=True)
    manifest.write_text(json.dumps({'created_files': created, 'created_directories': directories,
                                   'conditional_cleanup_directory': str(root.parent),
                                   'protected_tmp_root': str(root.parent.parent)}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'scenarios': ['dry-run-zero-writes', 'lock-contention', 'snapshot-new-arrival', 'delete-missing-page', 'rotation-reprepare', 'partial-append-block', 'real-preflight-append', 'CRLF-prefix', 'retry-idempotent', 'cleanup-report-only'], 'cleanup_manifest': str(manifest)}, ensure_ascii=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sandbox-root', required=True)
    run(Path(parser.parse_args().sandbox_root).resolve())
