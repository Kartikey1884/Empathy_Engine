# The Empathy Engine

Bring emotional intelligence to synthetic voices by mapping text sentiment to expressive speech.

## Features
- Sentiment-aware emotion detection using a Hugging Face transformer with intensity cues.
- Classifies text into positive, neutral, or negative emotional states.
- Intensity-driven modulation of **rate**, **volume**, and (driver permitting) **pitch**.
- Generated SSML payloads for cloud or SSML-compatible voices.
- Streamlit interface with instant playback, emotion metrics, and downloads.
- CLI for quick experimentation and FastAPI service for integration.
- Automatic audio file generation (`.wav`) with emotion-labelled filenames.

## Requirements
- Python 3.10+
- Windows voices already available to the operating system (via SAPI5 for `pyttsx3`).

Install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Set your Hugging Face access token (replace `hf_xxx` with your real token). You can either export `HF_TOKEN` (preferred) or `HUGGINGFACEHUB_API_TOKEN`, or place it in a `.env` file:

```powershell
setx HF_TOKEN "hf_xxx"
```

or create a `.env` file at the project root:

```
HF_TOKEN=hf_xxx
```

## Project Structure
```
empathy/
├── empathy_engine/
│   ├── __init__.py
│   ├── api.py             # FastAPI application
│   ├── cli.py             # Command-line entry point
│   ├── config.py          # Voice profile definitions
│   ├── emotion.py         # Emotion detection helpers
│   ├── service.py         # Orchestrates detection + speech
│   ├── speech.py          # Thin wrapper around pyttsx3
│   └── ssml.py            # SSML composition helpers
├── outputs/ (created on demand)
├── README.md
├── requirements.txt
└── streamlit_app.py      # Streamlit frontend
```

## How It Works
1. **Emotion detection** – `EmotionDetector` uses a Hugging Face `twitter-roberta-base` sentiment model plus simple punctuation/word emphasis cues to classify text as positive, neutral, or negative and compute an intensity score (0.0-1.0).
2. **Voice mapping** – Each emotion maps to a baseline `VoiceProfile` (rate, volume, pitch) with configurable modulation ranges.
3. **Intensity scaling** – Intensity interpolates within those ranges to keep positive delivery lively, neutral steady, and negative responses calmer.
4. **Speech synthesis** – `pyttsx3` renders expressive speech to `.wav` while defaults are restored for subsequent runs and a matching SSML document is produced.

## CLI Usage

Run the CLI via module execution:

```bash
python -m empathy_engine.cli --text "I'm thrilled about your progress!"
```

Options:
- `--text` – Inline text to convert.
- `--file` – Path to a UTF-8 text file.
- `--output` – Output directory (default: `outputs`).
- `--filename` – Custom filename (`.wav` assumed if omitted).
- `--ssml-file` – Optional path to save the generated SSML markup.

Example output:

```
Emotion: positive (intensity: 0.68)
Applied rate: 214 wpm
Applied volume: 1.02
Applied pitch: 80
Audio saved to: C:\Users\hp\Desktop\empathy\outputs\empathy_positive.wav
SSML saved to: C:\Users\hp\Desktop\empathy\outputs\empathy_positive.ssml
```

## Streamlit Frontend

Launch the interactive UI:

```bash
streamlit run streamlit_app.py
```

Features:
- Rich text editor for authoring customer dialogues or announcements.
- Real-time emotion, intensity, rate, volume, pitch, and baselines.
- Embedded audio playback with download support plus copyable SSML.

## API Usage

Start the FastAPI service:

```bash
uvicorn empathy_engine.api:app --reload
```

Send a request:

```bash
curl -X POST http://127.0.0.1:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "I am disappointed we missed the deadline.", "include_ssml": true}'
```

Sample response:

```json
{
  "emotion": "negative",
  "intensity": 0.61,
  "rate": 138,
  "volume": 0.68,
  "pitch": 46,
  "audio_path": "C:/Users/hp/Desktop/empathy/outputs/empathy_negative.wav",
  "ssml": "<speak ...>...</speak>"
}
```

## Design Notes
- **Emotion mapping**: Leverages the `cardiffnlp/twitter-roberta-base-sentiment-latest` model to obtain positive/neutral/negative probabilities.
- **Intensity scaling**: Intensity blends the model's top probability with punctuation/emphasis cues to tune modulation strength.
- **Prosody limits**: Rate deltas clamp between 120–200 wpm, volume stays within 0.3–1.0, pitch clamps to ≥30 to keep voices natural.
- **SSML**: Each response includes `<prosody>` adjustments for rate/volume/pitch, optional `<emphasis>` levels, and contextual `<break>` cues.
- **Pitch**: Many SAPI5 voices ignore custom pitch; failures are ignored so synthesis never aborts.

## Troubleshooting
- If synthesis fails, verify your OS has working text-to-speech voices and `pyttsx3` can initialize SAPI5.
- Provide a valid Hugging Face access token via `HF_TOKEN` (or `HUGGINGFACEHUB_API_TOKEN`); requests without it will raise an error.
- Enable debug logging (`set LOG_LEVEL=DEBUG`) to view Hugging Face request metadata when troubleshooting API calls.
- For better voices, swap in cloud providers; reuse `EmotionDetector` + parameter logic and swap the `SpeechSynthesizer` implementation.

## Next Steps
- Move to a dedicated Hugging Face Inference Endpoint for higher throughput and lower latency.
- Add speaker selection, multilingual voices, or cloud TTS providers that accept the generated SSML.
- Layer user-tunable style controls (energy, empathy slider) to override modulation spans at runtime.

