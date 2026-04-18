from __future__ import annotations

"""One-time script to pre-generate all filler/regex response audio files.

Usage:
    uv run generate-sounds              # generate missing files only
    uv run generate-sounds --force      # regenerate everything
"""

import argparse
import asyncio

from .config import load_settings
from .elevenlabs_client import ElevenLabsClient
from .regex_responses import GENERIC_FILLERS, OPENINGS, REGEX_RESPONSES


async def _generate_all(force: bool) -> None:
    settings = load_settings()
    sounds_dir = settings.sounds_dir
    sounds_dir.mkdir(parents=True, exist_ok=True)
    client = ElevenLabsClient(settings)

    entries: list[tuple[str, str]] = (
        [(text, slug) for text, slug in OPENINGS.values()]
        + [(text, slug) for _, text, slug in REGEX_RESPONSES]
        + [(text, slug) for text, slug in GENERIC_FILLERS]
    )

    to_generate = [
        (text, slug)
        for text, slug in entries
        if force or not (sounds_dir / f"{slug}.pcm").exists()
    ]

    if not to_generate:
        print(f"All {len(entries)} files already exist. Use --force to regenerate.")
        return

    print(f"Generating {len(to_generate)}/{len(entries)} audio files into {sounds_dir} ...")

    async def generate_one(text: str, slug: str) -> None:
        path = sounds_dir / f"{slug}.pcm"
        try:
            pcm = await client.synthesize_pcm(text)
            path.write_bytes(pcm)
            print(f"  ✓  {slug}.pcm  ({len(pcm) // 1024}KB)")
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗  {slug}  — {exc}")

    await asyncio.gather(*[generate_one(t, s) for t, s in to_generate])
    print("Done.")


def cli() -> None:
    parser = argparse.ArgumentParser(description="Pre-generate filler/response audio files.")
    parser.add_argument("--force", action="store_true", help="Regenerate even if files exist.")
    args = parser.parse_args()
    asyncio.run(_generate_all(force=args.force))


if __name__ == "__main__":
    cli()
