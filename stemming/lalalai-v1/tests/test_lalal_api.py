import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import lalal_api


class FakeResponse:
    def __init__(self, content, content_type="audio/mpeg", filename="track.mp3"):
        self.status_code = 200
        self.headers = {
            "Content-Type": content_type,
            "Content-Disposition": f'attachment; filename="{filename}"',
        }
        self._content = content

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def iter_content(self, _size):
        yield self._content


class AudioFormatTests(unittest.TestCase):
    def test_detects_mp3_wav_and_aac_from_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            mp3 = Path(directory) / "unknown.part"
            mp3.write_bytes(b"ID3" + b"\x00" * 64)
            wav = Path(directory) / "unknown2.part"
            wav.write_bytes(b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 32)
            aac = Path(directory) / "unknown3.part"
            aac.write_bytes(b"\xff\xf1" + b"\x00" * 64)
            self.assertEqual(lalal_api.detect_audio_extension(mp3), ".mp3")
            self.assertEqual(lalal_api.detect_audio_extension(wav), ".wav")
            self.assertEqual(lalal_api.detect_audio_extension(aac), ".aac")

    @patch("lalal_api.requests.get")
    def test_download_names_from_actual_returned_format(self, get):
        get.return_value = FakeResponse(b"ID3" + b"\x00" * 64)
        with tempfile.TemporaryDirectory() as directory:
            result = lalal_api.download_track(
                {"url": "https://download.example/track"},
                Path(directory),
                "song",
                "vocals",
                60,
                False,
            )
            self.assertEqual(result.name, "song_vocals_lalalai.mp3")
            self.assertFalse(any(Path(directory).glob("*.part")))

    @patch("lalal_api.requests.get")
    def test_rejects_declared_format_mismatch_without_final_file(self, get):
        get.return_value = FakeResponse(
            b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 32,
            content_type="audio/mpeg",
            filename="track.mp3",
        )
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(lalal_api.LalalError, "declared"):
                lalal_api.download_track(
                    {"url": "https://download.example/track"},
                    Path(directory),
                    "song",
                    "vocals",
                    60,
                    False,
                )
            self.assertEqual(list(Path(directory).iterdir()), [])


class ResumeTests(unittest.TestCase):
    def test_resume_reuses_valid_partial_stage_and_leaves_missing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            vocals = output / "song_vocals_lalalai.mp3"
            vocals.write_bytes(b"ID3" + b"\x00" * 64)
            resolved = lalal_api.resolve_outputs(
                output,
                "song",
                ["vocals", "instrumental"],
                resume=True,
                overwrite=False,
            )
            self.assertEqual(resolved["vocals"], vocals)
            self.assertIsNone(resolved["instrumental"])

    def test_normal_mode_rejects_existing_output_before_api_use(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "song_bass_lalalai.mp3").write_bytes(b"ID3" + b"\x00" * 64)
            with self.assertRaisesRegex(lalal_api.LalalError, "output exists"):
                lalal_api.resolve_outputs(
                    output,
                    "song",
                    ["bass", "no_bass"],
                    resume=False,
                    overwrite=False,
                )


class TaskTests(unittest.TestCase):
    @patch("lalal_api.api_request")
    def test_multiple_tasks_share_one_check_request(self, api_request):
        api_request.return_value = {
            "result": {
                "task-v": {
                    "status": "success",
                    "result": {"tracks": [{"label": "vocals"}]},
                },
                "task-d": {
                    "status": "success",
                    "result": {"tracks": [{"label": "drum"}]},
                },
            }
        }
        result = lalal_api.wait_for_tasks(
            {"vocals": "task-v", "drum": "task-d"},
            "key",
            60,
            1,
            True,
            lambda _seconds: None,
        )
        self.assertEqual(set(result), {"vocals", "drum"})
        self.assertEqual(api_request.call_count, 1)

    def test_pair_mapping_uses_api_labels(self):
        isolated, complement = lalal_api.select_track_pair(
            [{"label": "no_synthesizer"}, {"label": "synthesizer"}],
            "synthesizer",
        )
        self.assertEqual(isolated["label"], "synthesizer")
        self.assertEqual(complement["label"], "no_synthesizer")


if __name__ == "__main__":
    unittest.main()
