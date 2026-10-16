"""Synthetic video tests; filesystem mutation is mocked in unit tests."""
import argparse
import importlib.util
import math
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    'preprocess_video', Path(__file__).resolve().parents[1] / 'scripts' / 'preprocess_video.py')
video = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(video)


class SamplingTests(unittest.TestCase):
    def test_short_clip_includes_start_and_final_segment(self):
        times = video.sample_times(12)
        self.assertEqual(times[:3], [0, 5, 10])
        self.assertGreater(times[-1], 11)
        self.assertLess(times[-1], 12)

    def test_long_clip_is_bounded_and_covers_end(self):
        for duration in (300, 3600, 86400):
            times = video.sample_times(duration)
            self.assertEqual(len(times), 60)
            self.assertEqual(times[0], 0)
            self.assertGreater(times[-1], duration - 1)
            self.assertEqual(times, sorted(set(times)))

    def test_invalid_duration(self):
        for duration in (0, -1, math.nan, math.inf):
            with self.subTest(duration=duration), self.assertRaises(ValueError):
                video.sample_times(duration)

    def test_tiny_clip(self):
        self.assertTrue(all(0 <= t < .01 for t in video.sample_times(.01)))

    def test_low_fps_tail_stays_on_a_decodable_frame(self):
        self.assertEqual(video.sample_times(12, frame_interval=.5)[-1], 11.5)


class BoundaryTests(unittest.TestCase):
    def test_outside_scope_rejected(self):
        root = Path('/synthetic/raw').resolve()
        with self.assertRaises(ValueError):
            video.require_inside(root.parent / 'outside.mp4', root)

    def test_task_id(self):
        for task_id in ('../escape', '..', '.', 'a/b', 'a?b'):
            with self.subTest(task_id=task_id), self.assertRaises(ValueError):
                video.validate_task_id(task_id)
        video.validate_task_id('video-20261016-001')

    def test_no_video_is_zero_io(self):
        args = argparse.Namespace(no_video=True)
        with patch.object(video, 'validate_input') as validate, \
             patch.object(video, 'run_tool') as run, \
             patch.object(Path, 'mkdir') as mkdir, \
             patch.object(Path, 'read_bytes') as read:
            self.assertEqual(video.process(args), {'status': 'skipped', 'reason': '--no-video', 'writes': 0})
            for mock in (validate, run, mkdir, read):
                mock.assert_not_called()

    def test_missing_tools_do_not_create_artifacts(self):
        with patch.object(video.shutil, 'which', return_value=None), \
             patch.object(Path, 'mkdir') as mkdir, self.assertRaises(FileNotFoundError):
            video.find_tools()
        mkdir.assert_not_called()

    def test_input_and_output_real_path_boundaries(self):
        base = Path('/synthetic').absolute()
        cases = [dict(input=base / 'outside.mp4', source_scope=base / 'raw'),
                 dict(input=base / 'raw/clip.mp4', source_scope=base / 'outside'),
                 dict(input=base / 'raw/other/clip.mp4', source_scope=base / 'raw/specified')]
        for case in cases:
            args = argparse.Namespace(vault_root=base, task_id='check', **case)
            with patch.object(Path, 'resolve', lambda p, strict=False: p.absolute()), \
                 patch.object(Path, 'is_dir', return_value=True), \
                 patch.object(Path, 'mkdir') as mkdir, self.assertRaises(ValueError):
                video.validate_input(args)
            mkdir.assert_not_called()

    def test_resolved_link_escape_rejected(self):
        base = Path('/synthetic/raw').absolute()
        escaped = base.parent / 'outside.mp4'
        link = base / 'linked.mp4'
        with patch.object(Path, 'resolve', lambda p, strict=False: escaped if p == link else p.absolute()), \
             self.assertRaises(ValueError):
            video.require_inside(link, base)


class MediaTests(unittest.TestCase):
    def test_probe_rejects_audio_only_and_bad_duration(self):
        for metadata in ({'streams': [], 'format': {'duration': '12'}},
                         {'streams': [{'codec_type': 'video'}], 'format': {'duration': 'NaN'}}):
            with patch.object(video, 'run_tool', return_value=argparse.Namespace(stdout=video.json.dumps(metadata))), \
                 self.assertRaises(ValueError):
                video.probe('ffprobe', Path('/synthetic.mp4'))

    def test_subtitle_ambiguity_is_not_guessed(self):
        root = Path('/synthetic/raw').resolve()
        with patch.object(Path, 'is_file', return_value=True):
            result = video.subtitle_candidate(root / 'clip.mp4', root, root)
        self.assertEqual(result['status'], 'ambiguous')

    def test_subtitle_scope_is_not_expanded(self):
        root = Path('/synthetic/raw').resolve()
        with patch.object(Path, 'is_file', return_value=True):
            result = video.subtitle_candidate(root / 'clip.mp4', root, root / 'clip.mp4')
        self.assertEqual(result['status'], 'out_of_scope')

    def test_decode_failure_is_item_scoped(self):
        with patch.object(video, 'run_tool', side_effect=subprocess.CalledProcessError(1, ['ffmpeg'])):
            result = video.extract_frame('ffmpeg', Path('/clip.mp4'), Path('/frame.jpg'), 5, 0)
        self.assertEqual(result['status'], 'failed')
        self.assertIsNone(result['source_pts_seconds'])

    def test_decoded_pts_is_distinct_from_requested_time(self):
        output = '[Parsed_showinfo_1] n:   0 pts:   67 pts_time:5.58333 duration:1'
        with patch.object(video, 'run_tool', return_value=argparse.Namespace(stderr=output)), \
             patch.object(Path, 'is_file', return_value=True):
            result = video.extract_frame('ffmpeg', Path('/clip.mp4'), Path('/frame.jpg'), 5, 2)
        self.assertEqual(result['source_pts_seconds'], 5.58333)
        self.assertAlmostEqual(result['timeline_seconds'], 3.58333)
        self.assertEqual(result['requested_seconds'], 5)

    def test_unknown_pts_is_not_fabricated(self):
        with patch.object(video, 'run_tool', return_value=argparse.Namespace(stderr='')), \
             patch.object(Path, 'is_file', return_value=True):
            result = video.extract_frame('ffmpeg', Path('/clip.mp4'), Path('/frame.jpg'), 5, 0)
        self.assertEqual(result['status'], 'sampled_timestamp_unknown')
        self.assertIsNone(result['timeline_seconds'])


class LifecycleTests(unittest.TestCase):
    def execute(self, after='before'):
        root = Path('/synthetic').absolute()
        task = root / 'tmp/obsidian-llm-wiki/example'
        metadata = dict(duration_seconds=6, start_time_seconds=0, stream_index=0, frame_interval=.5)
        writes = []
        def write(path, value, **kwargs):
            writes.append((path, video.json.loads(value)))
        def extract(*args):
            return dict(status='failed', path=str(args[2]))
        with patch.object(video, 'validate_input', return_value=(root/'raw/clip.mp4',root/'raw',root/'raw',task,root/'tmp')), \
             patch.object(video, 'find_tools', return_value=('ffprobe','ffmpeg')), \
             patch.object(video, 'probe', return_value=metadata), \
             patch.object(video, 'digest', side_effect=['before',after]), \
             patch.object(video, 'subtitle_candidate', return_value={'status':'absent'}), \
             patch.object(video, 'extract_frame', side_effect=extract), \
             patch.object(Path, 'stat', return_value=argparse.Namespace(st_size=12)), \
             patch.object(Path, 'mkdir'), patch.object(Path, 'is_file', return_value=True), \
             patch.object(Path, 'write_text', write):
            result = video.process(argparse.Namespace(no_video=False))
        return result, writes

    def test_failed_decode_outputs_are_registered_for_cleanup(self):
        result, writes = self.execute()
        self.assertEqual(result['status'], 'unreadable')
        manifest = [data for path,data in writes if path.name == 'created_files.json'][-1]
        report = [data for path,data in writes if path.name == 'video-manifest.json'][-1]
        self.assertEqual(Path(manifest['created_files'][-1]).name, 'created_files.json')
        self.assertTrue(all(frame['path'] in manifest['created_files'] for frame in report['frames']))
        self.assertEqual(Path(manifest['created_directories'][0]).name, 'frames')

    def test_changed_source_invalidates_evidence(self):
        result, _ = self.execute(after='changed')
        self.assertEqual(result['status'], 'source_changed')
        self.assertFalse(result['source_unchanged'])


if __name__ == '__main__':
    unittest.main()
