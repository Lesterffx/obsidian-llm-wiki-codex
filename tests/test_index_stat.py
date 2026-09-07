"""Synthetic regression cases; no private vault data or filesystem writes.

Run: <project-python> -B -m unittest discover -s tests -v
"""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "references" / "index_stat.py"
SPEC = importlib.util.spec_from_file_location("index_stat", SCRIPT)
stat = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stat)


class ResolutionTests(unittest.TestCase):
    def setUp(self):
        self.pages = ["wiki/标题.md", "wiki/分类/标题.md", "wiki/分类/唯一页.md"]

    def test_three_forms_and_extensions(self):
        for target in ("wiki/分类/唯一页", "分类/唯一页", "唯一页",
                       "wiki/分类/唯一页.md", "分类/唯一页.md", "唯一页.md",
                       "wiki\\分类\\唯一页"):
            with self.subTest(target=target):
                self.assertEqual(stat.resolve_target(target, self.pages),
                                 ("wiki/分类/唯一页.md", None))

    def test_explicit_root_wins_over_same_stem(self):
        for target in ("wiki/标题", "wiki/标题.md"):
            with self.subTest(target=target):
                self.assertEqual(stat.resolve_target(target, self.pages),
                                 ("wiki/标题.md", None))

    def test_bare_title_remains_ambiguous(self):
        resolved, reason = stat.resolve_target("标题", self.pages)
        self.assertIsNone(resolved)
        self.assertIn("歧义", reason)

    def test_nested_path_wins(self):
        self.assertEqual(stat.resolve_target("分类/标题", self.pages),
                         ("wiki/分类/标题.md", None))

    def test_missing_path_retains_stem_fallback(self):
        self.assertEqual(stat.resolve_target("旧分类/唯一页", self.pages),
                         ("wiki/分类/唯一页.md", None))

    def test_unknown_title(self):
        self.assertEqual(stat.resolve_target("不存在", self.pages), (None, "未命中"))

    def test_exclusions_and_duplicate_aliases(self):
        resolved, broken, counts = stat.resolve_targets(
            ["wiki/分类/唯一页", "唯一页", "raw/原图.md", "图.canvas",
             "图.png", "页面标题", "https://example.invalid/page"], self.pages)
        self.assertEqual(resolved, {"wiki/分类/唯一页.md"})
        self.assertEqual(broken, [])
        self.assertEqual(sum(n - 1 for n in counts.values()), 1)


class SyntheticVaultTests(unittest.TestCase):
    # In-memory mini vault exercises parsing, domain count, aggregation and footer
    # comparison together without creating or removing directories.
    schema = "# Schema\n## 领域注册表\n| 领域 | raw | wiki |\n|---|---|---|\n| 示例 | raw/示例/ | wiki/示例/ |\n"
    pages = ["wiki/示例/甲.md", "wiki/示例/乙.md"]
    rows = "| [[wiki/示例/甲|别名]] | 摘要 |\n| [[示例/甲#小节]] | 摘要 |\n| [[raw/材料.md]] | 来源 |\n| [[图.canvas]] | 画布 |\n"
    footer = "_统计：1 个已索引页面 | 2 个 Wiki 文件 | 1 个注册领域 | 上次更新于 2000-01-01_\n> 索引健康：未收录 1 | Markdown 断链 0 | 重复条目 1\n"

    def payload(self, index):
        def read(path):
            return index if path.name == "index.md" else self.schema
        with patch.object(stat, "read_utf8", side_effect=read), \
             patch.object(stat, "scan_wiki", return_value=self.pages), \
             patch.object(Path, "is_file", return_value=True):
            return stat.build_payload(Path("synthetic-vault"))

    def test_six_counts_and_matching_footer(self):
        result = self.payload(self.rows + self.footer)
        keys = ("indexed_page_count", "wiki_file_count", "registered_domain_count",
                "missing_count", "broken_count", "duplicate_count")
        self.assertEqual(tuple(result[k] for k in keys), (1, 2, 1, 1, 0, 1))
        self.assertTrue(result["footer_match"])

    def test_footer_drift(self):
        result = self.payload(self.rows + self.footer.replace("1 个已索引", "2 个已索引"))
        self.assertFalse(result["footer_match"])
        self.assertEqual(result["drift"]["indexed_page_count"], {"footer": 2, "scan": 1})

    def test_missing_footer(self):
        result = self.payload(self.rows)
        self.assertFalse(result["footer_match"])
        self.assertIsNone(result["footer"])

    def test_code_fences_are_excluded(self):
        result = self.payload(self.rows + "```markdown\n| [[不存在]] | 示例 |\n```\n" + self.footer)
        self.assertEqual(result["broken"], [])

    def test_broken_detail_shape(self):
        result = self.payload(self.rows + "| [[不存在]] | 摘要 |\n" + self.footer)
        self.assertEqual(result["broken"], [{"target": "不存在", "reason": "未命中"}])
        self.assertEqual(result["broken_count"], 1)


if __name__ == "__main__":
    unittest.main()
