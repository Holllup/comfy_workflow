import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np


FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")


def _probe(path: Path) -> dict:
    result = subprocess.run(
        [FFPROBE, "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def _tone(frequency: int, seconds: float, sample_rate: int = 32000) -> dict:
    t = np.arange(round(seconds * sample_rate), dtype=np.float32) / sample_rate
    wave = 0.2 * np.sin(2 * np.pi * frequency * t)
    return {"waveform": np.stack([wave, wave])[None], "sample_rate": sample_rate}


@unittest.skipUnless(FFMPEG and FFPROBE, "ffmpeg and ffprobe required")
class AVMediaTests(unittest.TestCase):
    def test_join_uses_each_clip_frame_count_and_keeps_audio_cut_in_order(self):
        from cat_vlog_h3.core import encode_av_clip, join_av_clips
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths, counts = [], [39, 56, 22]
            for index, count in enumerate(counts):
                frames = np.zeros((count, 32, 64, 3), dtype=np.float32)
                frames[..., index] = 0.85
                path = root / f"{index}.mp4"
                encode_av_clip(frames, _tone(330 + index * 330, count / 24), path)
                paths.append(path)
            target = root / 'mixed.mp4'
            join_av_clips(paths, target, frame_counts=counts, output_size=(32, 18))
            info = _probe(target)
            video = next(stream for stream in info['streams'] if stream['codec_type'] == 'video')
            self.assertEqual(int(video['nb_read_frames']), sum(counts))
            self.assertLessEqual(abs(float(info['format']['duration']) - sum(counts) / 24), 1 / 24)
            pcm = subprocess.check_output([FFMPEG, '-v', 'error', '-i', str(target), '-f', 'f32le', '-ac', '1', '-ar', '48000', 'pipe:1'])
            waveform = np.frombuffer(pcm, dtype='<f4')
            offset = 0
            for index, count in enumerate(counts):
                begin = round((offset / 24 + 0.2) * 48000)
                part = waveform[begin:begin + 4800]
                frequency = np.argmax(np.abs(np.fft.rfft(part))) * 48000 / len(part)
                self.assertAlmostEqual(frequency, 330 + index * 330, delta=10)
                offset += count

    def test_encodes_video_with_synchronized_ambient_audio(self):
        try:
            from cat_vlog_h3.core import encode_av_clip
        except ImportError as exc:
            self.fail(f"Audio-video encoding is missing: {exc}")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "shot.mp4"
            frames = np.zeros((48, 32, 64, 3), dtype=np.float32)
            frames[..., 0] = 0.8
            encode_av_clip(frames, _tone(440, 1.95), path, fps=24)
            info = _probe(path)
            video = next(stream for stream in info["streams"] if stream["codec_type"] == "video")
            audio = next(stream for stream in info["streams"] if stream["codec_type"] == "audio")
            self.assertEqual(video["codec_name"], "h264")
            self.assertEqual(int(video["nb_read_frames"]), 48)
            self.assertEqual(audio["codec_name"], "aac")
            self.assertLessEqual(abs(float(info["format"]["duration"]) - 2.0), 1 / 24)

    def test_join_preserves_clip_order_and_audio_length(self):
        try:
            from cat_vlog_h3.core import encode_av_clip, join_av_clips
        except ImportError as exc:
            self.fail(f"Audio-video joining is missing: {exc}")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            clips = []
            for index, color in enumerate((0, 2), 1):
                frames = np.zeros((24, 32, 64, 3), dtype=np.float32)
                frames[..., color] = 0.85
                path = root / f"shot_{index}.mp4"
                encode_av_clip(frames, _tone(440 if index == 1 else 880, 1.0), path, fps=24)
                clips.append(path)
            final = root / "final.mp4"
            join_av_clips(clips, final, fps=24, frames_per_clip=24, output_size=(32, 18))
            info = _probe(final)
            video = next(stream for stream in info["streams"] if stream["codec_type"] == "video")
            self.assertEqual(int(video["nb_read_frames"]), 48)
            self.assertTrue(any(stream["codec_type"] == "audio" for stream in info["streams"]))
            self.assertLessEqual(abs(float(info["format"]["duration"]) - 2.0), 1 / 24)
            raw = subprocess.check_output([
                FFMPEG, "-v", "error", "-i", str(final), "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1",
            ])
            decoded = np.frombuffer(raw, dtype=np.uint8).reshape(48, 18, 32, 3)
            self.assertGreater(decoded[3, :, :, 0].mean(), decoded[3, :, :, 2].mean() + 100)
            self.assertGreater(decoded[30, :, :, 2].mean(), decoded[30, :, :, 0].mean() + 100)


if __name__ == "__main__":
    unittest.main()
