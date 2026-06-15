"""Plain data containers shared across the pipeline."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class TokenInfo:
    """One token produced by the morphological analyzer."""
    surface: str          # text as it appears in the script, e.g. "中田"
    reading: str          # hiragana reading guessed by the analyzer, e.g. "なかた"
    pos: List[str] = field(default_factory=list)  # part-of-speech tuple from Sudachi
    is_oov: bool = False  # True if the analyzer did not know this word

    @property
    def is_proper_noun(self) -> bool:
        # Sudachi marks proper nouns (names, places, orgs) with 固有名詞
        return "固有名詞" in self.pos


@dataclass
class WordEntry:
    """A confirmed surface -> reading mapping headed for a list."""
    surface: str
    reading: str          # hiragana
    pos: str = ""
    source: str = ""      # "fixed" | "general" | "confirmed"
    note: str = ""