"""Text-to-speech engine using edge-tts (Microsoft Edge online TTS)."""

from __future__ import annotations

import asyncio
import os
import tempfile
import threading
from pathlib import Path

from loguru import logger

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

try:
    from PySide6.QtCore import QUrl
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    HAS_QT_MEDIA = True
except ImportError:
    HAS_QT_MEDIA = False


class TTSEngine:
    """Text-to-speech using edge-tts with Qt multimedia playback."""

    DEFAULT_VOICE = "zh-CN-XiaoyiNeural"

    def __init__(self, voice: str | None = None, enabled: bool = True):
        self._voice = voice or self.DEFAULT_VOICE
        self._enabled = enabled and HAS_EDGE_TTS
        self._player: QMediaPlayer | None = None
        self._audio_output: QAudioOutput | None = None
        self._cache_dir = Path(tempfile.gettempdir()) / "nix_tts_cache"
        self._cache_dir.mkdir(exist_ok=True)

        if not HAS_EDGE_TTS:
            logger.warning("edge-tts not installed, TTS disabled (pip install edge-tts)")

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value and HAS_EDGE_TTS

    def _ensure_player(self):
        if self._player is None and HAS_QT_MEDIA:
            self._player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._player.setAudioOutput(self._audio_output)

    async def _synthesize(self, text: str) -> str | None:
        """Generate speech audio file. Returns file path or None."""
        if not HAS_EDGE_TTS:
            return None
        try:
            safe_name = "".join(c if c.isalnum() else "_" for c in text[:30])
            output_path = str(self._cache_dir / f"{safe_name}.mp3")

            if os.path.exists(output_path):
                return output_path

            communicate = edge_tts.Communicate(text, self._voice)
            await communicate.save(output_path)
            logger.debug("TTS saved: {}", output_path)
            return output_path
        except Exception as e:
            logger.error("TTS synthesis failed: {}", e)
            return None

    def speak(self, text: str):
        """Speak text asynchronously (non-blocking)."""
        if not self._enabled or not text.strip():
            return

        def _run():
            try:
                audio_path = asyncio.run(self._synthesize(text))
                if audio_path:
                    self._play_audio(audio_path)
            except Exception as e:
                logger.error("TTS speak failed: {}", e)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def _play_audio(self, path: str):
        """Play audio file using Qt multimedia or fallback."""
        self._ensure_player()
        if self._player and HAS_QT_MEDIA:
            try:
                from PySide6.QtCore import QTimer
                url = QUrl.fromLocalFile(path)
                QTimer.singleShot(0, lambda: self._qt_play(url))
                return
            except Exception:
                pass
        self._fallback_play(path)

    def _qt_play(self, url: QUrl):
        if self._player:
            self._player.setSource(url)
            self._player.play()

    @staticmethod
    def _fallback_play(path: str):
        """Fallback: play via system command."""
        try:
            import subprocess
            subprocess.Popen(
                ["powershell", "-c", f'(New-Object Media.SoundPlayer "{path}").PlaySync()'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            logger.debug("Fallback audio play failed: {}", e)

    def stop(self):
        if self._player:
            self._player.stop()

    @staticmethod
    def available_voices() -> list[str]:
        """Return a curated list of Chinese/English voices."""
        return [
            "zh-CN-XiaoyiNeural",
            "zh-CN-YunxiNeural",
            "zh-CN-YunjianNeural",
            "zh-CN-XiaoxiaoNeural",
            "en-US-JennyNeural",
            "en-US-GuyNeural",
            "ja-JP-NanamiNeural",
        ]

    def cleanup_cache(self):
        """Remove cached audio files."""
        for f in self._cache_dir.glob("*.mp3"):
            try:
                f.unlink()
            except OSError:
                pass
