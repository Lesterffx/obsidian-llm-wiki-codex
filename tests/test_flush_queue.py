"""虚构数据测试；文件系统边界用 mock，不产生或删除测试运行目录。"""
import argparse
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch, mock_open

SPEC = importlib.util.spec_from_file_location('flush_queue', Path(__file__).resolve().parents[1] / 'scripts' / 'flush_queue.py')
queue = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(queue)


def entry(title='optimize | 示例（id-1）', body='示例变更'):
    return '## [2026-09-13] ' + title + '\n\n- 范围：示例。\n- 变更：' + body + '。\n- 维护：检查。\n- 验证：通过。\n'


def fixture(task='optimize', page='wiki/示例.md'):
    row = '' if task == 'delete' else '| [[示例]] | 摘要 | 标签 |'
    return ('<!-- obsidian-llm-wiki queue v1 -->\n'
            '<!-- task: ' + task + ' -->\n<!-- date: 2026-09-13 -->\n'
            '<!-- page: ' + page + ' -->\n<!-- section: ## 示例 -->\n<!-- summary: 示例 -->\n'
            '<!-- index-entry -->\n' + row + '\n<!-- /index-entry -->\n'
            '<!-- log-entry -->\n' + entry(task + ' | 示例（id-1）') + '<!-- /log-entry -->\n').encode('utf-8')


class LogTests(unittest.TestCase):
    def test_lf_crlf_exact_prefix_and_newline(self):
        for before in (b'# log\n', b'# log\r\n', b'# log'):
            payload = queue.pending_entries(before, [entry()])
            self.assertTrue((before + payload).startswith(before))
            self.assertTrue(payload.endswith(b'\n'))
            self.assertEqual(b'\r\n' in payload, b'\r\n' in before)

    def test_order(self):
        a, b = entry('ingest | a'), entry('sync | b')
        output = queue.pending_entries(b'# log\n', [a, b]).decode()
        self.assertLess(output.index('ingest'), output.index('sync'))

    def test_full_duplicate_noop(self):
        self.assertEqual(queue.pending_entries(entry().encode(), [entry()]), b'')

    def test_same_title_different_content_blocked(self):
        with self.assertRaises(ValueError):
            queue.pending_entries(entry().encode(), [entry(body='不同')])

    def test_partial_entry_blocked(self):
        with self.assertRaises(ValueError):
            queue.pending_entries(entry()[:50].encode(), [entry()])

    def test_repeated_title_blocked(self):
        with self.assertRaises(ValueError):
            queue.pending_entries((entry() + '\n' + entry()).encode(), [entry()])

    def test_duplicate_in_batch_deduplicated(self):
        self.assertEqual(queue.pending_entries(b'', [entry(), entry()]).decode().count('## ['), 1)

    def test_heading_must_be_exact(self):
        self.assertNotEqual(queue.pending_entries(b'# quoted ' + entry().encode(), [entry()]), b'')

    def test_invalid_log(self):
        for text in ('', entry().replace('2026-09-13', '2026-99-99'), entry().replace('- 验证：通过。', ''), entry() + entry()):
            with self.subTest(text=text), self.assertRaises(ValueError):
                queue.log_entry(text)

    def test_invalid_utf8(self):
        with self.assertRaises(UnicodeError):
            queue.pending_entries(b'\xff', [entry()])

    def test_resume_states(self):
        before, payload = b'# log\r\n', entry().encode()
        state = dict(before_size=len(before), before_sha=queue.digest(before), payload=payload.decode())
        self.assertEqual(queue.validate_payload(before, state), (False, True))
        self.assertEqual(queue.validate_payload(before + payload, state), (True, False))
        for corrupt in (before + payload[:20], before + b'external', b'bad' + payload):
            self.assertEqual(queue.validate_payload(corrupt, state), (False, False))


class FragmentTests(unittest.TestCase):
    def parse(self, data, exists=True):
        vault = Path('/synthetic-vault').resolve()
        with patch.object(queue, 'safe_file'), patch.object(queue, 'inside', side_effect=lambda root, path: path), \
             patch.object(Path, 'read_bytes', return_value=data), patch.object(Path, 'is_file', return_value=exists), \
             patch.object(Path, 'exists', return_value=exists):
            return queue.fragment(vault, vault / 'logs/queue/example.md')

    def test_five_commands_and_legacy_format(self):
        for task in queue.TASKS:
            with self.subTest(task=task):
                self.assertEqual(self.parse(fixture(task))['task'], task)

    def test_delete_absent_page_and_empty_row(self):
        self.assertEqual(self.parse(fixture('delete'), False)['page_sha256'], None)

    def test_ordinary_missing_page_blocked(self):
        with self.assertRaises(ValueError):
            self.parse(fixture(), False)

    def test_invalid_fields_and_fences(self):
        for data in (fixture().replace(b'<!-- task: optimize -->', b''), fixture('migrate'),
                     fixture().replace(b'<!-- /log-entry -->', b''),
                     fixture().replace(b'<!-- date: 2026-09-13 -->', b'<!-- date: 2026-09-12 -->'),
                     fixture().replace(b'<!-- summary: ', b'<!-- task: '), b'\xff'):
            with self.subTest(data=data), self.assertRaises((ValueError, UnicodeError)):
                self.parse(data)

    def test_traversal_and_nonwiki_blocked(self):
        for page in ('wiki/../raw/x.md', 'raw/x.md', 'wiki/x.txt', '../wiki/x.md'):
            with self.subTest(page=page), self.assertRaises(ValueError):
                self.parse(fixture(page=page))

    def test_real_containment(self):
        root = Path('/synthetic-root').resolve()
        with self.assertRaises(ValueError):
            queue.inside(root, root.parent / 'escape')

    def test_symlink_rejected(self):
        with patch.object(Path, 'is_symlink', return_value=True), self.assertRaises(ValueError):
            queue.inside(Path('/root'), Path('/root/queue'))

    def test_dry_run_does_not_write(self):
        args = argparse.Namespace(vault_root='/synthetic', dry_run=True)
        with patch.object(Path, 'is_dir', return_value=True), patch.object(queue, 'safe_file'), \
             patch.object(queue, 'inside', side_effect=lambda root, path: path), \
             patch.object(queue, 'inspect', return_value=([], [])), patch.object(Path, 'open') as opened, \
             patch.object(Path, 'mkdir') as mkdir:
            result = queue.execute(args)
            self.assertEqual(result['writes'], 0)
            opened.assert_not_called()
            mkdir.assert_not_called()

    def test_live_or_stale_lock_never_auto_removed(self):
        args = argparse.Namespace(vault_root='/synthetic', dry_run=False, phase='acquire')
        with patch.object(Path, 'is_dir', return_value=True), patch.object(queue, 'safe_file'), \
             patch.object(queue, 'inside', side_effect=lambda root, path: path), \
             patch.object(Path, 'mkdir'), patch.object(Path, 'open', side_effect=FileExistsError), \
             patch.object(Path, 'unlink') as unlink, self.assertRaises(ValueError):
            queue.execute(args)
        unlink.assert_not_called()

    def test_wrong_owner(self):
        with patch.object(queue, 'safe_file'), patch.object(Path, 'read_text', return_value='{"token":"owner"}'), self.assertRaises(ValueError):
            queue.owned(Path('/lock'), 'intruder')

    def test_snapshot_change_blocks(self):
        with patch.object(queue, 'fragment', return_value={'file': 'x', 'sha256': 'new'}), self.assertRaises(ValueError):
            queue.unchanged(Path('/vault'), [{'file': 'x', 'sha256': 'old'}])


if __name__ == '__main__':
    unittest.main()
