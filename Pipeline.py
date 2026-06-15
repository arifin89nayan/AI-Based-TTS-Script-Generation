"""
Pipeline orchestrator — runs the whole diagram (steps 1 -> 13).

Flow:
  2  extract kanji words
  3  match against Fixed List           ─┐
  4  classify unmatched words            │ loop while the
  5  is Confirmation List empty?         │ Confirmation List
  6/7  human review -> save to Fixed List┘ is NOT empty
  8  build General List (current script only)
  9  merge Fixed (used here) + General
  10 TTS List
  11 build Azure SSML
  12/13 synthesize MP3
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, List

import Analyzer as analyzer
import Config as configclear
from AzureTTS import synthesize
from FixedList import FixedList
from Models import TokenInfo
from Review import review_confirmation_list
from Ssml import build_ssml


def _needs_confirmation(tok: TokenInfo) -> bool:
    """Diagram step 4: which unmatched words a human must check.

    A word is risky (and goes to the Confirmation List) when it is a proper
    noun (place/person/org name), unknown to the analyzer, or has no reading.
    Everything else is trusted to the analyzer and goes to the General List.
    Tune this rule to your domain.
    """
    return tok.is_proper_noun or tok.is_oov or not tok.reading


@dataclass
class PipelineResult:
    ssml: str
    tts_map: Dict[str, str]
    general_list: Dict[str, str] = field(default_factory=dict)
    audio_path: str = ""


class TTSPipeline:
    def __init__(self, fixed_list: FixedList):
        self.fixed = fixed_list

    def run(
        self,
        script_text: str,                       # step 1: Original Script Input
        out_path: str = "output.mp3",
        synthesize_audio: bool = True,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ) -> PipelineResult:
        # Step 2: extract every distinct kanji-containing word.
        kanji_words = analyzer.extract_kanji_words(script_text)

        general_candidates: List[TokenInfo] = []

        # Steps 3-7 loop: keep confirming risky words until none remain.
        while True:
            general_candidates = []
            confirmation: List[TokenInfo] = []

            for tok in kanji_words:
                # Step 3: already confirmed in the Fixed List? -> resolved.
                if self.fixed.contains(tok.surface):
                    continue
                # Step 4: classify the unmatched word.
                if _needs_confirmation(tok):
                    confirmation.append(tok)
                else:
                    general_candidates.append(tok)

            # Step 5: Confirmation List empty? Yes -> leave the loop.
            if not confirmation:
                break

            # Steps 6 & 7: human checks readings, confirmed terms saved to
            # the Fixed List, then we loop back to step 3 (re-match).
            review_confirmation_list(confirmation, self.fixed, input_fn, output_fn)

        # Step 8: General List from remaining words (this script only).
        general_list = {t.surface: t.reading for t in general_candidates if t.reading}

        # Step 9 + 10: merge Fixed entries used here with the General List -> TTS List.
        fixed_used = {
            t.surface: self.fixed.get(t.surface)
            for t in kanji_words
            if self.fixed.contains(t.surface)
        }
        tts_map = {**fixed_used, **general_list}

        # Step 11: generate the Azure SSML script with confirmed readings.
        ssml = build_ssml(script_text, tts_map, config.AZURE_VOICE, config.SPEECH_LANG)

        result = PipelineResult(ssml=ssml, tts_map=tts_map, general_list=general_list)

        # Steps 12 & 13: feed Azure, get audio data.
        if synthesize_audio:
            result.audio_path = synthesize(
                ssml,
                out_path,
                config.AZURE_SPEECH_KEY,
                config.AZURE_SPEECH_REGION,
                config.AZURE_AUDIO_FORMAT,
            )
        return result
