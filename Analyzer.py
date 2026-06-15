"""
Morphological analysis layer (diagram step 2).

Uses SudachiPy to split Japanese text into tokens, attach a hiragana reading
to each, and pull out the words that contain kanji (the only ones Azure can
mispronounce).
"""
from typing import List

import jaconv
from sudachipy import dictionary, tokenizer

from Models import TokenInfo

# Split mode C = longest units. Best for keeping names/compounds in one piece.
_MODE = tokenizer.Tokenizer.SplitMode.C
_tokenizer = dictionary.Dictionary(dict="core").create()

# CJK ideograph ranges (covers common + extension A kanji).
_KANJI_RANGES = ((0x3400, 0x4DBF), (0x4E00, 0x9FFF))


def contains_kanji(text: str) -> bool:
    for ch in text:
        code = ord(ch)
        if any(lo <= code <= hi for lo, hi in _KANJI_RANGES):
            return True
    return False


def _to_hiragana(katakana_reading: str) -> str:
    if not katakana_reading or katakana_reading == "*":
        return ""
    return jaconv.kata2hira(katakana_reading)


def tokenize(text: str) -> List[TokenInfo]:
    """Return every token of the text, in order, with reading + POS info."""
    tokens = []
    for m in _tokenizer.tokenize(text, _MODE):
        tokens.append(
            TokenInfo(
                surface=m.surface(),
                reading=_to_hiragana(m.reading_form()),
                pos=list(m.part_of_speech()),
                is_oov=m.is_oov(),
            )
        )
    return tokens


def extract_kanji_words(text: str) -> List[TokenInfo]:
    """
    Diagram step 2: unique kanji-containing words from the script.
    De-duplicated by surface so each distinct word is reviewed once.
    """
    seen = set()
    result = []
    for tok in tokenize(text):
        if contains_kanji(tok.surface) and tok.surface not in seen:
            seen.add(tok.surface)
            result.append(tok)
    return result