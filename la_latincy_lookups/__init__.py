"""Latin lookup tables for LatinCy spaCy pipelines.

Provides lemma_lookup table (~910K entries) via spaCy's lookup entry point
system. Sources: Kaikki Wiktionary, UD treebanks.

Usage:
    from spacy.lookups import load_lookups
    lookups = load_lookups(lang="la", tables=["lemma_lookup"])
    table = lookups.get_table("lemma_lookup")
"""

__version__ = "1.0.0"

from importlib.resources import files


def _get_file(filename: str):
    return files(__name__).joinpath("data", filename)


la = {
    "lemma_lookup": _get_file("la_lemma_lookup.json"),
}
