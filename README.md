# AI-Based-TTS-Script-Generation-

AI-Based TTS Script Generation is a system that converts museum or educational content into clean, structured, and pronunciation-aware scripts for text-to-speech audio generation. It supports text correction, dictionary-based term handling, audio script preparation, and quality checking for accurate narration output.

## Overview

The pipeline takes a Japanese script, finds kanji words whose pronunciation Azure TTS could get wrong, resolves the correct reading (from a saved dictionary, an analyzer guess, or a human reviewer), and produces Azure SSML that forces the correct pronunciation before synthesizing the final MP3.

## How it works

1. **Extract kanji words** from the input script using SudachiPy morphological analysis (`Analyzer.py`).
2. **Match against the Fixed List** — a persistent Excel-backed dictionary of previously confirmed surface → reading pairs (`FixedList.py`).
3. **Classify unmatched words** as safe (analyzer's guess is trusted) or risky (proper nouns, out-of-vocabulary words, or missing readings).
4. **Human review** of risky words via the CLI — accept the suggested reading or type a correction; confirmed entries are saved back to the Fixed List (`Review.py`).
5. **Build the TTS List** by merging Fixed List entries with newly confirmed readings.
6. **Generate Azure SSML**, wrapping each resolved word in `<sub alias="reading">` so Azure reads the confirmed hiragana instead of guessing (`Ssml.py`).
7. **Synthesize audio** via Azure Cognitive Services Speech SDK, producing an MP3 file (`AzureTTS.py`).

The full flow is orchestrated by `Pipeline.py` (`TTSPipeline.run`).

## Project structure

| Module | Purpose |
| --- | --- |
| `Main.py` | CLI entry point — script/SSML input, TTS list import, audio output |
| `Pipeline.py` | Orchestrates the end-to-end pipeline |
| `Analyzer.py` | Tokenizes text and extracts kanji words (SudachiPy + jaconv) |
| `FixedList.py` | Excel-backed dictionary of confirmed word readings |
| `Review.py` | CLI human review for unresolved/risky words |
| `Ssml.py` | Builds Azure SSML with pronunciation overrides |
| `AzureTTS.py` | Calls Azure Cognitive Services to synthesize MP3 audio |
| `Models.py` | Shared data classes (`TokenInfo`, `WordEntry`) |
| `Config.py` | Central configuration (Azure credentials, voice, paths) |

## Requirements

- Python 3.13+
- [SudachiPy](https://github.com/WorksApplications/SudachiPy) + a Sudachi core dictionary
- `jaconv`
- `openpyxl`
- `azure-cognitiveservices-speech`

## Configuration

Set the following environment variables (see `Config.py` for defaults):

- `AZURE_SPEECH_KEY` — Azure Speech resource key
- `AZURE_SPEECH_REGION` — Azure Speech resource region (e.g. `japaneast`)
- `AZURE_VOICE` — TTS voice name (e.g. `ja-JP-NanamiNeural`)
- `FIXED_LIST_EXCEL` — path to the Fixed List `.xlsx` dictionary file

## Usage

```bash
# Read a script file, review interactively, produce MP3
python Main.py --script story.txt --out story.mp3

# Use a ChatGPT TTS list directly (skip human review)
python Main.py --script story.txt --tts-list tts.txt --out story.mp3

# Dry run with ChatGPT list (build SSML only, no audio)
python Main.py --script story.txt --tts-list tts.txt --no-audio

# Synthesize directly from an SSML file
python Main.py --ssml my_script.ssml --out story.mp3

# Dry run: build SSML and show the TTS List without calling Azure
python Main.py --script story.txt --no-audio
```

### TTS list file format

Markdown table (e.g. exported from ChatGPT):

```
| Kanji | Hiragana |
| ----- | -------- |
| 漢字   | かんじ    |
```

Or plain, one entry per line:

```
漢字,かんじ
漢字 -> かんじ
```
