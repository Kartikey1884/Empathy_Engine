"""Configuration primitives for the Empathy Engine."""

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class VoiceProfile:
    """Represents how the TTS engine should be modulated for a given emotion."""

    label: str
    rate: int
    volume: float
    pitch: int | None = None  # pyttsx3 pitch support is engine-dependent
    rate_delta_range: Tuple[int, int] = (0, 0)
    volume_delta_range: Tuple[float, float] = (0.0, 0.0)
    pitch_delta_range: Tuple[int, int] | None = None


@dataclass(frozen=True)
class EmotionMapping:
    """Maps emotion labels to voice profiles."""

    profiles: Dict[str, VoiceProfile]

    def get(self, emotion: str) -> VoiceProfile:
        normalized = emotion.lower()
        if normalized not in self.profiles:
            raise KeyError(f"No voice profile configured for emotion '{emotion}'")
        return self.profiles[normalized]

