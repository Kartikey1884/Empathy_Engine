"""Utilities for detecting emotions from text."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Iterable, Literal, Sequence

from dotenv import load_dotenv
import requests


EmotionLabel = Literal["positive", "neutral", "negative"]


EMPHASIS_WORDS: Sequence[str] = (
    "really",
    "very",
    "so",
    "extremely",
    "incredibly",
)


@dataclass(frozen=True)
class EmotionResult:
    label: EmotionLabel
    intensity: float


class EmotionDetector:
    """Sentiment detector backed by Hugging Face Inference API."""

    def __init__(
        self,
        model_id: str = "cardiffnlp/twitter-roberta-base-sentiment-latest",
        *,
        token: str | None = None,
        env_vars: Iterable[str] = ("HF_TOKEN", "HUGGINGFACEHUB_API_TOKEN"),
        timeout: float = 10.0,
    ) -> None:
        self._model_id = model_id
        load_dotenv()

        self._token = token or self._resolve_token(env_vars)
        if not self._token:
            joined = ", ".join(env_vars)
            raise RuntimeError(
                f"Set one of the following environment variables for the Hugging Face API token: {joined}."
            )

        self._logger = logging.getLogger(__name__)
        self._logger.debug("Initializing EmotionDetector with model '%s'", self._model_id)

        self._timeout = timeout
        self._endpoint = (
            "https://router.huggingface.co/hf-inference/models/" + self._model_id
        )
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )
        self._logger.debug("Using Hugging Face endpoint %s", self._endpoint)

    def detect(self, text: str) -> EmotionResult:
        if not text or not text.strip():
            return EmotionResult(label="neutral", intensity=0.0)

        cleaned = " ".join(text.strip().split())
        preview = cleaned[:160] + ("…" if len(cleaned) > 160 else "")
        self._logger.debug("Submitting text for sentiment (%d chars): %s", len(cleaned), preview)

        payload = {
            "inputs": cleaned,
            "options": {"wait_for_model": True, "use_cache": True},
        }

        try:
            response = self._session.post(
                self._endpoint,
                json=payload,
                timeout=self._timeout,
            )
            self._logger.debug("HF status=%s request-id=%s",
                                response.status_code,
                                response.headers.get("x-request-id"))
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:  # pragma: no cover - network errors
            self._logger.exception("Call to Hugging Face inference failed")
            raise RuntimeError("Failed to classify sentiment via Hugging Face API") from exc

        if isinstance(data, dict) and "error" in data:
            self._logger.error("Hugging Face API error response: %s", data)
            raise RuntimeError(f"Hugging Face API error: {data['error']}")

        if not data:
            self._logger.error("Hugging Face API returned an empty response")
            raise RuntimeError("Hugging Face API returned an empty response")

        first_item = data[0]
        if isinstance(first_item, list):
            flat_scores = first_item
        elif isinstance(first_item, dict) and "label" in first_item:
            flat_scores = data
        else:
            self._logger.error("Unexpected response format from Hugging Face API: %s", data)
            raise RuntimeError("Unexpected response format from Hugging Face API")

        score_map = {item["label"].lower(): float(item["score"]) for item in flat_scores}
        self._logger.debug("Score map: %s", score_map)

        positive_score = score_map.get("positive") or score_map.get("label_2", 0.0)
        neutral_score = score_map.get("neutral") or score_map.get("label_1", 0.0)
        negative_score = score_map.get("negative") or score_map.get("label_0", 0.0)

        if positive_score >= max(neutral_score, negative_score):
            label: EmotionLabel = "positive"
            primary_score = positive_score
        elif negative_score >= max(positive_score, neutral_score):
            label = "negative"
            primary_score = negative_score
        else:
            label = "neutral"
            primary_score = neutral_score

        exclamations = cleaned.count("!")
        question = "?" in cleaned
        emphasis_terms = sum(
            cleaned.lower().count(word) for word in EMPHASIS_WORDS
        )

        intensity_bonus = min(
            0.3,
            0.06 * exclamations + 0.05 * emphasis_terms + (0.03 if question else 0.0),
        )
        intensity = min(1.0, primary_score + intensity_bonus)
        self._logger.debug(
            "Detected emotion=%s intensity=%.3f (base=%.3f, bonus=%.3f)",
            label,
            intensity,
            primary_score,
            intensity_bonus,
        )

        return EmotionResult(label=label, intensity=intensity)

    def _resolve_token(self, env_vars: Iterable[str]) -> str | None:
        for name in env_vars:
            value = os.getenv(name)
            if value:
                return value
        return None

