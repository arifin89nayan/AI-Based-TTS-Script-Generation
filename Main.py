"""
Command-line entry point.

Examples:
    # Read a script file, review interactively, produce MP3:
    python Main.py --script story.txt --out story.mp3

    # Use a ChatGPT TTS list directly (skip human review):
    python Main.py --script story.txt --tts-list tts.txt --out story.mp3

    # Dry run with ChatGPT list (build SSML only, no audio):
    python Main.py --script story.txt --tts-list tts.txt --no-audio

    # Synthesize directly from an SSML file:
    python Main.py --ssml my_script.ssml --out story.mp3

    # Dry run: build SSML and show the TTS List without calling Azure:
    python Main.py --script story.txt --no-audio

TTS list file format — Markdown table (from ChatGPT):
    | Kanji | Hiragana |
    | ----- | -------- |
    | 漢字   | かんじ    |

Or plain one-per-line:
    漢字,かんじ
    漢字 -> かんじ
"""
import argparse
import re
import sys
from typing import Dict

import Config as config
from AzureTTS import synthesize
from FixedList import FixedList
from Pipeline import TTSPipeline
from Ssml import build_ssml


def _parse_tts_list(path: str) -> Dict[str, str]:
    """Parse a ChatGPT TTS list file into a surface->reading dict.

    Accepts Markdown table format:
        | Kanji | Hiragana |
        | ----- | -------- |
        | 漢字   | かんじ    |

    Or plain one-entry-per-line formats:
        漢字,かんじ
        漢字 -> かんじ
        漢字\tかんじ
    Lines starting with # and blank lines are ignored.
    """
    result: Dict[str, str] = {}
    plain_sep = re.compile(r" -> |,|\t")
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("|"):
                # Markdown table row: | col1 | col2 |
                cells = [c.strip() for c in line.strip("|").split("|")]
                if len(cells) < 2:
                    continue
                surface, reading = cells[0], cells[1]
                # skip header or separator rows
                if not surface or set(surface) <= set("- "):
                    continue
                # skip column-header row (contains only ASCII/latin text)
                if surface.isascii():
                    continue
                if surface and reading:
                    result[surface] = reading
            else:
                parts = plain_sep.split(line, maxsplit=1)
                if len(parts) == 2:
                    surface, reading = parts[0].strip(), parts[1].strip()
                    if surface and reading:
                        result[surface] = reading
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="TTS script generation & voice confirmation agent")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--script", help="Path to a plain-text UTF-8 file (runs full pipeline).")
    group.add_argument("--ssml", help="Path to an SSML file — sent directly to Azure, skipping the pipeline.")
    parser.add_argument("--tts-list", dest="tts_list",
                        help="ChatGPT TTS list file (surface,reading per line). Used with --script to skip human review.")
    parser.add_argument("--out", default="output.mp3", help="Output MP3 path.")
    parser.add_argument("--excel", default=config.FIXED_LIST_EXCEL, help="Fixed List Excel (.xlsx) file.")
    parser.add_argument("--no-audio", action="store_true", help="Build SSML only; skip Azure (ignored with --ssml).")
    args = parser.parse_args(argv)

    # --- Direct SSML -> MP3 path ---
    if args.ssml:
        with open(args.ssml, encoding="utf-8") as f:
            ssml_text = f.read()
        if not ssml_text.strip():
            print("SSML file is empty.", file=sys.stderr)
            return 1
        audio_path = synthesize(
            ssml_text,
            args.out,
            config.AZURE_SPEECH_KEY,
            config.AZURE_SPEECH_REGION,
            config.AZURE_AUDIO_FORMAT,
        )
        print(f"Audio written to: {audio_path}")
        return 0

    # --- Full pipeline path ---
    if args.script:
        with open(args.script, encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("No input script provided.", file=sys.stderr)
        return 1

    # --- ChatGPT TTS list path: skip human review, use provided mappings ---
    if args.tts_list:
        tts_map = _parse_tts_list(args.tts_list)
        ssml = build_ssml(text, tts_map, config.AZURE_VOICE, config.SPEECH_LANG)
        print("\n--- TTS List (surface -> reading) ---")
        for surface, reading in tts_map.items():
            print(f"  {surface} -> {reading}")
        print("\n--- SSML ---")
        print(ssml)
        if not args.no_audio:
            audio_path = synthesize(
                ssml,
                args.out,
                config.AZURE_SPEECH_KEY,
                config.AZURE_SPEECH_REGION,
                config.AZURE_AUDIO_FORMAT,
            )
            print(f"\nAudio written to: {audio_path}")
        return 0

    fixed = FixedList(args.excel)
    try:
        pipeline = TTSPipeline(fixed)
        result = pipeline.run(
            text,
            out_path=args.out,
            synthesize_audio=not args.no_audio,
        )
    finally:
        fixed.close()

    print("\n--- TTS List (surface -> reading) ---")
    for surface, reading in result.tts_map.items():
        print(f"  {surface} -> {reading}")
    print("\n--- SSML ---")
    print(result.ssml)
    if result.audio_path:
        print(f"\nAudio written to: {result.audio_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())