"""Speech synthesis helpers built on top of pyttsx3."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pyttsx3


class SpeechSynthesizer:
    def __init__(self, voice_id: Optional[str] = None) -> None:
        self._engine = pyttsx3.init()
        if voice_id is not None:
            self._engine.setProperty("voice", voice_id)

        self._default_rate = self._engine.getProperty("rate")
        self._default_volume = self._engine.getProperty("volume")

    def synthesize(
        self,
        text: str,
        *,
        rate: Optional[int] = None,
        volume: Optional[float] = None,
        pitch: Optional[int] = None,
        destination: str | Path,
    ) -> Path:
        destination_path = Path(destination).resolve()

        if rate is not None:
            self._engine.setProperty("rate", int(rate))

        if volume is not None:
            bounded_volume = max(0.0, min(1.0, float(volume)))
            self._engine.setProperty("volume", bounded_volume)

        if pitch is not None:
            try:
                # Not all drivers expose pitch, so failure is non-fatal.
                self._engine.setProperty("pitch", int(pitch))
            except Exception:
                pass

        self._engine.save_to_file(text, str(destination_path))
        self._engine.runAndWait()

        # Restore defaults to avoid state bleed between requests.
        self._engine.setProperty("rate", self._default_rate)
        self._engine.setProperty("volume", self._default_volume)

        return destination_path

