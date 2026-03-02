"""Speech-to-text stub using system microphone input.

Full implementation requires whisper or Azure Speech SDK.
This module provides the interface and a basic fallback.
"""

from __future__ import annotations

import threading
from typing import Callable

from loguru import logger


class STTEngine:
    """Speech-to-text interface. Currently a stub for future integration."""

    def __init__(self, on_result: Callable[[str], None] | None = None):
        self._on_result = on_result
        self._listening = False

    @property
    def is_listening(self) -> bool:
        return self._listening

    def start_listening(self):
        """Begin capturing microphone input."""
        if self._listening:
            return
        self._listening = True
        logger.info("STT listening started (stub)")

        def _listen():
            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    logger.info("Listening...")
                    audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
                try:
                    text = recognizer.recognize_google(audio, language="zh-CN")
                    logger.info("STT result: {}", text)
                    if self._on_result:
                        self._on_result(text)
                except sr.UnknownValueError:
                    logger.debug("STT could not understand audio")
                except sr.RequestError as e:
                    logger.error("STT service error: {}", e)
            except ImportError:
                logger.warning(
                    "speech_recognition not installed. "
                    "Install via: pip install SpeechRecognition pyaudio"
                )
            except Exception as e:
                logger.error("STT failed: {}", e)
            finally:
                self._listening = False

        thread = threading.Thread(target=_listen, daemon=True)
        thread.start()

    def stop_listening(self):
        self._listening = False
