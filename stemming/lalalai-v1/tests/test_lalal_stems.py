import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from os import environ
from pathlib import Path
from unittest.mock import patch

import lalal_stems


class StemRequestTests(unittest.TestCase):
    def test_aliases_and_multiple_requests(self):
        self.assertEqual(
            lalal_stems.expand_stems(
                ["vi", "drums", "synth", "eguitar", "aguitar", "bass"]
            ),
            [
                "vocals",
                "drum",
                "synthesizer",
                "electric_guitar",
                "acoustic_guitar",
                "bass",
            ],
        )

    def test_all_expands_all_musical_stems(self):
        self.assertEqual(
            lalal_stems.expand_stems(["all"]), list(lalal_stems.ALL_STEMS)
        )

    def test_model_compatibility_is_actionable(self):
        with self.assertRaisesRegex(lalal_stems.LalalError, "use --splitter auto"):
            lalal_stems.validate_model(["strings"], "andromeda")

    def test_auto_accepts_all_stems(self):
        lalal_stems.validate_model(list(lalal_stems.ALL_STEMS), "auto")


class DryRunTests(unittest.TestCase):
    def _run(self, stems):
        with tempfile.TemporaryDirectory() as directory:
            audio = Path(directory) / "song.wav"
            audio.write_bytes(b"RIFF" + b"\x00" * 4 + b"WAVE")
            output = StringIO()
            errors = StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                result = lalal_stems.main([str(audio), *stems, "--dry-run"])
            return result, output.getvalue(), errors.getvalue()

    def test_single_alias_multiple_and_all_variants(self):
        variants = (
            (["vocals"], "Billable split count: 1"),
            (["vi"], "vocals + instrumental"),
            (["vocals", "drums", "bass"], "Billable split count: 3"),
            (["all"], f"Billable split count: {len(lalal_stems.ALL_STEMS)}"),
        )
        for stems, expected in variants:
            with self.subTest(stems=stems):
                result, output, errors = self._run(stems)
                self.assertEqual(result, 0)
                self.assertIn(expected, output)
                self.assertEqual(errors, "")


class OrchestrationTests(unittest.TestCase):
    @patch("lalal_stems.download_track")
    @patch("lalal_stems.wait_for_tasks")
    @patch("lalal_stems.start_stem_task")
    @patch("lalal_stems.upload_file")
    def test_multiple_stems_upload_once(
        self, upload_file, start_stem_task, wait_for_tasks, download_track
    ):
        upload_file.return_value = "source-id"
        start_stem_task.side_effect = lambda _source, stem, *_args: f"task-{stem}"
        wait_for_tasks.return_value = {
            "vocals": [
                {"label": "vocals", "url": "v"},
                {"label": "no_vocals", "url": "nv"},
            ],
            "drum": [
                {"label": "drum", "url": "d"},
                {"label": "no_drum", "url": "nd"},
            ],
            "bass": [
                {"label": "bass", "url": "b"},
                {"label": "no_bass", "url": "nb"},
            ],
        }
        download_track.side_effect = (
            lambda _track, output, source, label, *_args: output
            / f"{source}_{label}_lalalai.mp3"
        )
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            environ, {"LALAL_LICENSE": "key"}, clear=True
        ):
            audio = Path(directory) / "song.wav"
            audio.write_bytes(b"RIFF" + b"\x00" * 4 + b"WAVE")
            result = lalal_stems.main(
                [str(audio), "vocals", "drums", "bass", "--quiet"]
            )
        self.assertEqual(result, 0)
        upload_file.assert_called_once()
        self.assertEqual(start_stem_task.call_count, 3)
        self.assertEqual(download_track.call_count, 6)


if __name__ == "__main__":
    unittest.main()
