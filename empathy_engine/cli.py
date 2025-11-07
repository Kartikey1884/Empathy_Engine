"""Command-line interface for the Empathy Engine."""

from __future__ import annotations

from pathlib import Path

import click

from .service import EmpathyEngine


@click.command()
@click.option("--text", "text_input", type=str, help="Text to convert to empathetic speech.")
@click.option("--file", "file_path", type=click.Path(exists=True, dir_okay=False), help="Path to a file whose contents will be spoken.")
@click.option("--output", "output_dir", type=click.Path(dir_okay=True, file_okay=False), default="outputs", show_default=True, help="Directory to write audio files to.")
@click.option("--filename", type=str, help="Optional filename for the rendered audio (defaults to emotion-based name).")
@click.option(
    "--ssml-file",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Optional path to store generated SSML markup.",
)
def main(
    text_input: str | None,
    file_path: str | None,
    output_dir: str,
    filename: str | None,
    ssml_file: str | None,
) -> None:
    """Convert text to empathetic speech and save the audio file."""

    if not text_input and not file_path:
        raise click.BadParameter("Provide --text or --file for input.")

    if text_input and file_path:
        raise click.BadParameter("Please supply either --text or --file, not both.")

    if file_path:
        text_to_speak = Path(file_path).read_text(encoding="utf-8").strip()
    else:
        text_to_speak = text_input.strip() if text_input else ""

    if not text_to_speak:
        raise click.BadParameter("Input text is empty after trimming.")

    engine = EmpathyEngine(output_directory=output_dir)
    response = engine.speak_to_file(text_to_speak, filename=filename)

    click.echo(
        "Emotion: {label} (intensity: {intensity:.2f})\n"
        "Applied rate: {rate} wpm\n"
        "Applied volume: {volume:.2f}\n"
        "Applied pitch: {pitch}\n"
        "Audio saved to: {path}".format(
            label=response.emotion.label,
            intensity=response.emotion.intensity,
            rate=response.applied_rate,
            volume=response.applied_volume,
            pitch=response.applied_pitch if response.applied_pitch is not None else "driver default",
            path=response.audio_path,
        )
    )

    if ssml_file:
        output_path = Path(ssml_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(response.ssml, encoding="utf-8")
        click.echo(f"SSML saved to: {output_path.resolve()}")


if __name__ == "__main__":  # pragma: no cover
    main()

