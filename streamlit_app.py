"""Streamlit UI for the Empathy Engine."""

from __future__ import annotations

import uuid
from pathlib import Path

import streamlit as st

from empathy_engine import EmpathyEngine


st.set_page_config(
    page_title="Empathy Engine",
    page_icon="🎙️",
    layout="wide",
)


@st.cache_resource(show_spinner=False)
def get_engine() -> EmpathyEngine:
    return EmpathyEngine()


engine = get_engine()

st.title("The Empathy Engine")
st.subheader("Give your AI a human voice with sentiment-aware speech synthesis.")

with st.sidebar:
    st.header("How it works")
    st.markdown(
        """
        1. Paste or type any message.
        2. The Empathy Engine classifies the emotion and intensity.
        3. Speech is synthesized with dynamic rate, volume, and pitch adjustments.

        Use the controls below to experiment with different tones and copy the resulting audio.
        """
    )
    st.info("Tip: Longer sentences yield more expressive results.")


prompt = st.text_area(
    "Voice your message",
    placeholder="Share your latest customer update, feedback, or announcement...",
    height=200,
)


col1, col2 = st.columns([1, 1])

with col1:
    synthesize_clicked = st.button("Generate Empathetic Speech", type="primary", use_container_width=True)

with col2:
    clear_clicked = st.button("Clear", use_container_width=True)

if clear_clicked:
    st.experimental_rerun()


if synthesize_clicked:
    cleaned_prompt = prompt.strip()
    if not cleaned_prompt:
        st.warning("Please provide some text before synthesizing.")
    else:
        with st.spinner("Detecting emotion and creating expressive audio..."):
            unique_name = f"ui_{uuid.uuid4().hex}.wav"
            response = engine.speak_to_file(cleaned_prompt, filename=unique_name)
            audio_bytes = Path(response.audio_path).read_bytes()

        st.success("Audio ready! 🎧")

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("Emotion", response.emotion.label.replace("_", " ").title())
        metric_col2.metric("Intensity", f"{response.emotion.intensity:.2f}")
        metric_col3.metric("Pitch", response.applied_pitch or "driver default")

        st.caption("Positive, neutral, or negative tone adjusts rate, volume, and pitch based on intensity.")

        rate_col, volume_col = st.columns(2)
        rate_col.write(
            f"**Applied rate:** {response.applied_rate} wpm (baseline {response.voice_profile.rate} wpm)"
        )
        volume_col.write(
            f"**Applied volume:** {response.applied_volume:.2f} (baseline {response.voice_profile.volume:.2f})"
        )

        st.audio(audio_bytes, format="audio/wav")

        st.download_button(
            label="Download audio",
            data=audio_bytes,
            file_name=Path(response.audio_path).name,
            mime="audio/wav",
        )

        with st.expander("Generated SSML"):
            st.code(response.ssml, language="xml")
            st.download_button(
                label="Download SSML",
                data=response.ssml.encode("utf-8"),
                file_name=Path(response.audio_path).with_suffix(".ssml").name,
                mime="application/ssml+xml",
                key=f"ssml_{unique_name}",
            )

