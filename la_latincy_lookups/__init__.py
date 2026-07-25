"""Latin lookup tables for LatinCy NLP pipelines.

Provides a lemma_lookup table (~1.5M entries) as a flat surface-form -> lemma
JSON, discoverable by spaCy via the ``spacy_lookups`` entry point. Sources:
Kaikki Wiktionary, UD treebanks.

spaCy usage (entry-point discovery):
    from spacy.lookups import load_lookups
    lookups = load_lookups(lang="la", tables=["lemma_lookup"])
    table = lookups.get_table("lemma_lookup")

Framework-agnostic usage (Stanza / UDPipe / Flair — no spaCy required):
    from la_latincy_lookups import apply_lemma_lookup
    lemma = apply_lemma_lookup(word.text, word.upos, is_sent_start,
                               word.lemma)  # default mode="fallback"
"""

from importlib.resources import files

from .lemmatize import MODES, apply_lemma_lookup, load_lemma_lookup

__all__ = ["la", "MODES", "apply_lemma_lookup", "load_lemma_lookup"]


def _get_file(filename: str):
    return files(__name__).joinpath("data", filename)


la = {
    "lemma_lookup": _get_file("la_lemma_lookup.json"),
}
