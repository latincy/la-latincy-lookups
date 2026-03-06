"""Latin lookup tables for LatinCy spaCy pipelines.

Provides lemma_lookup table (948K entries) via spaCy's lookup entry point
system. Sources: Kaikki Wiktionary, UD treebanks, CLTK.

Usage:
    from spacy.lookups import load_lookups
    lookups = load_lookups(lang="la", tables=["lemma_lookup"])
    table = lookups.get_table("lemma_lookup")
"""

from importlib.resources import files


def _get_file(filename: str):
    return files(__name__).joinpath("data", filename)


la = {
    "lemma_lookup": _get_file("la_lemma_lookup.json"),
}
