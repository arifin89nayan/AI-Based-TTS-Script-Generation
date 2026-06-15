"""
Human review of the Confirmation List (diagram steps 6 -> 7).

Each risky word is shown with the analyzer's best-guess reading. The reviewer
presses Enter to accept it, or types the correct hiragana to override. Every
decision is saved into the Fixed List so it is never asked again.

`input_fn` / `output_fn` are injected so this can be driven by a CLI, a test,
or swapped for a web form later without changing the logic.
"""
from typing import Callable, List

from FixedList import FixedList
from Models import TokenInfo


def review_confirmation_list(
    items: List[TokenInfo],
    fixed_list: FixedList,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> None:
    output_fn(f"\n=== Human review: {len(items)} word(s) need confirmation ===")
    output_fn("Press Enter to accept the suggested reading, or type the correct hiragana.\n")

    for tok in items:
        suggested = tok.reading or "(none — reading required)"
        prompt = f"  {tok.surface}  [{suggested}] > "
        answer = input_fn(prompt).strip()

        if answer:
            reading = answer
        elif tok.reading:
            reading = tok.reading
        else:
            # No suggestion and no input: keep asking until we get a reading,
            # because an empty reading would let Azure guess again.
            while not answer:
                answer = input_fn(f"  Reading required for {tok.surface} > ").strip()
            reading = answer

        fixed_list.add(
            surface=tok.surface,
            reading=reading,
        )
        output_fn(f"    saved: {tok.surface} -> {reading}")