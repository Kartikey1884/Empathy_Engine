"""Simple FastAPI app that exposes the empathy engine as an HTTP service."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .service import EmpathyEngine


app = FastAPI(title="Empathy Engine", version="1.0.0")
_engine = EmpathyEngine()


class SynthesisRequest(BaseModel):
    text: str = Field(..., min_length=1, description="The text to convert into speech.")
    filename: str | None = Field(None, description="Optional filename for the output audio file.")
    include_ssml: bool = Field(True, description="Return generated SSML markup in the response.")


class SynthesisResponse(BaseModel):
    emotion: str
    intensity: float
    rate: int
    volume: float
    pitch: int | None
    audio_path: str
    ssml: str | None


@app.post("/synthesize", response_model=SynthesisResponse)
def synthesize(request: SynthesisRequest) -> SynthesisResponse:
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Input text is empty.")

    response = _engine.speak_to_file(text, filename=request.filename)

    return SynthesisResponse(
        emotion=response.emotion.label,
        intensity=response.emotion.intensity,
        rate=response.applied_rate,
        volume=response.applied_volume,
        pitch=response.applied_pitch,
        audio_path=str(Path(response.audio_path).resolve()),
        ssml=response.ssml if request.include_ssml else None,
    )

