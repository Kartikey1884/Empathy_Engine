"""Helpers for generating SSML markup for synthesized speech."""

from __future__ import annotations

import html
from dataclasses import dataclass
from xml.etree.ElementTree import Element, SubElement, tostring

from .config import VoiceProfile
from .emotion import EmotionResult


def _rate_percentage(baseline: int, applied: int) -> int:
    if baseline <= 0:
        return 100
    return max(50, min(200, int(round((applied / baseline) * 100))))


def _volume_descriptor(volume: float) -> str:
    if volume >= 0.95:
        return "x-loud"
    if volume >= 0.85:
        return "loud"
    if volume >= 0.7:
        return "medium"
    if volume >= 0.5:
        return "soft"
    return "x-soft"


def _pitch_step(profile_pitch: int | None, applied_pitch: int | None) -> str:
    if profile_pitch is None or applied_pitch is None:
        return "default"
    offset = applied_pitch - profile_pitch
    if offset == 0:
        return "default"
    semitone = max(-20, min(20, offset))
    sign = "+" if semitone > 0 else ""
    return f"{sign}{semitone}st"


@dataclass
class SSMLComposer:
    """Builds SSML documents tailored to an emotion response."""

    namespace: str = "http://www.w3.org/2001/10/synthesis"

    def build(
        self,
        *,
        text: str,
        emotion: EmotionResult,
        profile: VoiceProfile,
        applied_rate: int,
        applied_volume: float,
        applied_pitch: int | None,
    ) -> str:
        safe_text = html.escape(text.strip())

        root = Element("speak", attrib={"xmlns": self.namespace, "version": "1.0"})

        prosody_attrs = {
            "rate": f"{_rate_percentage(profile.rate, applied_rate)}%",
            "volume": _volume_descriptor(applied_volume),
        }

        pitch_descriptor = _pitch_step(profile.pitch, applied_pitch)
        if pitch_descriptor != "default":
            prosody_attrs["pitch"] = pitch_descriptor

        prosody = SubElement(root, "prosody", attrib=prosody_attrs)

        if emotion.intensity >= 0.65:
            emphasis = SubElement(prosody, "emphasis", attrib={"level": "strong"})
            emphasis.text = safe_text
        elif emotion.intensity >= 0.35:
            emphasis = SubElement(prosody, "emphasis", attrib={"level": "moderate"})
            emphasis.text = safe_text
        else:
            prosody.text = safe_text

        if emotion.label == "negative":
            SubElement(prosody, "break", attrib={"time": "250ms"})
        elif emotion.label == "positive" and emotion.intensity >= 0.5:
            SubElement(prosody, "break", attrib={"strength": "medium"})

        return tostring(root, encoding="unicode")

