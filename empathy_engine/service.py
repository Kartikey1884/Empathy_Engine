"""Core orchestration logic for the Empathy Engine."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import EmotionMapping, VoiceProfile
from .emotion import EmotionDetector, EmotionResult
from .speech import SpeechSynthesizer
from .ssml import SSMLComposer


def _default_mapping() -> EmotionMapping:
    return EmotionMapping(
        profiles={
            "positive": VoiceProfile(
                label="positive",
                rate=186,
                volume=0.95,
                pitch=70,
                rate_delta_range=(0, 45),
                volume_delta_range=(0.0, 0.12),
                pitch_delta_range=(0, 12),
            ),
            "neutral": VoiceProfile(
                label="neutral",
                rate=175,
                volume=0.88,
                pitch=64,
                rate_delta_range=(-5, 5),
                volume_delta_range=(-0.04, 0.04),
                pitch_delta_range=(-3, 4),
            ),
            "negative": VoiceProfile(
                label="negative",
                rate=160,
                volume=0.8,
                pitch=58,
                rate_delta_range=(0, -40),
                volume_delta_range=(0.0, -0.15),
                pitch_delta_range=(0, -12),
            ),
        }
    )


@dataclass
class EmpathyResponse:
    audio_path: Path
    emotion: EmotionResult
    voice_profile: VoiceProfile
    applied_rate: int
    applied_volume: float
    applied_pitch: Optional[int]
    ssml: str


class EmpathyEngine:
    """High-level API that maps emotion to expressive speech synthesis."""

    def __init__(
        self,
        *,
        mapping: Optional[EmotionMapping] = None,
        detector: Optional[EmotionDetector] = None,
        synthesizer: Optional[SpeechSynthesizer] = None,
        composer: Optional[SSMLComposer] = None,
        output_directory: str | Path = "outputs",
    ) -> None:
        self._mapping = mapping or _default_mapping()
        self._detector = detector or EmotionDetector()
        self._synthesizer = synthesizer or SpeechSynthesizer()
        self._composer = composer or SSMLComposer()
        self._output_directory = Path(output_directory).resolve()
        self._output_directory.mkdir(parents=True, exist_ok=True)

    def speak_to_file(self, text: str, *, filename: Optional[str] = None) -> EmpathyResponse:
        emotion = self._detector.detect(text)
        profile = self._mapping.get(emotion.label)

        rate, volume, pitch = self._modulate_parameters(profile, emotion)

        output_filename = filename or self._build_filename(emotion.label)
        destination = self._output_directory / output_filename

        audio_path = self._synthesizer.synthesize(
            text,
            rate=rate,
            volume=volume,
            pitch=pitch,
            destination=destination,
        )

        ssml = self._composer.build(
            text=text,
            emotion=emotion,
            profile=profile,
            applied_rate=rate,
            applied_volume=volume,
            applied_pitch=pitch,
        )

        return EmpathyResponse(
            audio_path=audio_path,
            emotion=emotion,
            voice_profile=profile,
            applied_rate=rate,
            applied_volume=volume,
            applied_pitch=pitch,
            ssml=ssml,
        )

    def _build_filename(self, emotion_label: str) -> str:
        sanitized = emotion_label.replace(" ", "_")
        return f"empathy_{sanitized}.wav"

    def _modulate_parameters(
        self, profile: VoiceProfile, emotion: EmotionResult
    ) -> tuple[int, float, Optional[int]]:
        intensity = emotion.intensity

        rate_delta = self._interpolate(profile.rate_delta_range, intensity)
        volume_delta = self._interpolate(profile.volume_delta_range, intensity)

        modulated_rate = max(120, int(round(profile.rate + rate_delta)))
        modulated_volume = max(0.3, min(1.0, profile.volume + volume_delta))

        pitch = profile.pitch
        if pitch is not None and profile.pitch_delta_range is not None:
            pitch_delta = self._interpolate(profile.pitch_delta_range, intensity)
            pitch = int(max(30, round(pitch + pitch_delta)))

        return modulated_rate, modulated_volume, pitch

    @staticmethod
    def _interpolate(delta_range: tuple[float, float], intensity: float) -> float:
        start, end = delta_range
        return start + (end - start) * intensity

