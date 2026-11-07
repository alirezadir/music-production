import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from os import environ
from pathlib import Path
from unittest.mock import patch

import remake_stems


class RemakeDryRunTests(unittest.TestCase):
    def test_dry_run_does_not_require_license(self):
        with tempfile.TemporaryDirectory() as directory:
            audio = Path(directory) / "song.wav"
            audio.write_bytes(b"RIFF" + b"\x00" * 4 + b"WAVE")
            output = StringIO()
            errors = StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                result = remake_stems.main([str(audio), "--dry-run"])
            self.assertEqual(result, 0)
            self.assertIn("instrumental_melodics", output.getvalue())
            self.assertEqual(errors.getvalue(), "")


class RemakeWorkflowTests(unittest.TestCase):
    @patch("remake_stems._run_stage")
    def test_preserves_four_stage_dependencies(self, run_stage):
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            environ, {"LALAL_LICENSE": "key"}, clear=True
        ):
            root = Path(directory)
            audio = root / "song.wav"
            audio.write_bytes(b"RIFF" + b"\x00" * 4 + b"WAVE")
            instrumental = root / "song_instrumental_lalalai.mp3"
            no_drums = root / "song_instrumental_no_drums_lalalai.mp3"
            run_stage.side_effect = (
                {"vocals": root / "vocals.mp3", "instrumental": instrumental},
                {"drums": root / "drums.mp3", "instrumental_no_drums": no_drums},
                {
                    "bass": root / "bass.mp3",
                    "instrumental_no_bass": root / "no_bass.mp3",
                },
                {"instrumental_melodics": root / "melodics.mp3"},
            )
            result = remake_stems.main([str(audio), "--quiet"])
        self.assertEqual(result, 0)
        self.assertEqual(run_stage.call_count, 4)
        self.assertEqual(
            run_stage.call_args_list[0].args[1:4],
            ("vocals", "vocals", "instrumental"),
        )
        self.assertEqual(
            run_stage.call_args_list[1].args[0:4],
            (instrumental, "drum", "drums", "instrumental_no_drums"),
        )
        self.assertEqual(
            run_stage.call_args_list[2].args[0:4],
            (instrumental, "bass", "bass", "instrumental_no_bass"),
        )
        self.assertEqual(
            run_stage.call_args_list[3].args[0:4],
            (no_drums, "bass", None, "instrumental_melodics"),
        )

if __name__ == "__main__":
    unittest.main()
