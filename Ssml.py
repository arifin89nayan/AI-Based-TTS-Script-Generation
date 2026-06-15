"""
Azure TTS script generation (diagram step 11).

Re-tokenizes the original script and wraps every kanji word that appears in
the TTS List with <sub alias="reading">, forcing Azure to read the confirmed
hiragana instead of guessing. Words not in the list pass through unchanged
(kana/punctuation are unambiguous to Azure already).
"""
from typing import Dict
from xml.sax.saxutils import escape, quoteattr

from Analyzer import tokenize


def build_ssml(text: str, tts_map: Dict[str, str], voice: str, lang: str) -> str:
    # Remove characters that should not be spoken
    text = text.replace("?", "").replace("？", "").replace("「", "").replace("」", "")
    parts = []
    for tok in tokenize(text):
        reading = tts_map.get(tok.surface)
        if reading:
            # alias is read aloud instead of the surface text
            parts.append(f"<sub alias={quoteattr(reading)}>{escape(tok.surface)}</sub>")
        else:
            parts.append(escape(tok.surface))
    body = "".join(parts)

    return (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xml:lang="{lang}">'
        f'<voice name="{voice}">{body}</voice>'
        f"</speak>"
    )