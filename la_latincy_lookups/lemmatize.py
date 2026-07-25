"""Framework-agnostic lemma-lookup overlay for LatinCy.

This generalizes latincy-pipelines' spaCy ``make_lookup_lemmatizer_function``
(``latincy-pipelines/scripts/functions.py``) so that *any* tool exposing
per-token ``(text, upos, is_sent_start, predicted_lemma)`` — Stanza, UDPipe,
Flair — can apply the same surface-form -> lemma dictionary as a
post-prediction overlay, with a single source of truth.

Design notes
------------
* **Pure standard library.** Importing this module does NOT require spaCy;
  that keeps it usable inside the torch/stanza/flair venvs without dragging
  spaCy (thinc/blis/pydantic) into them. spaCy is only needed by spaCy itself,
  which discovers the shipped table via the ``spacy_lookups`` entry point.
* **Lemma-only.** Unlike the spaCy function (which also rewrites PUNCT POS),
  this never touches POS — in the target frameworks POS comes from separate
  models/columns we must not clobber.
* **Injectable table.** ``apply_lemma_lookup`` accepts an optional ``table`` so
  experiments can swap alternative dictionaries (homograph-excluded, POS-keyed,
  long-tail-only) into the same harness without changing callers. The default
  is the shipped surface-form -> lemma table (case-sensitive).

Modes (the ``mode`` argument) form a coverage/caution gradient for ablation:

* ``"off"``       - return the model lemma unchanged (raw baseline).
* ``"fallback"``  - only fill from the table when the model punted (empty lemma
                    or an identity copy of the surface form). Minimal risk.
* ``"pos_gated"`` - table override for every hit EXCEPT proper nouns.
* ``"override"``  - table override on every hit (spaCy parity). Max coverage.

All non-``off`` modes apply the same final normalization spaCy does: lowercase
the initial character of a non-PROPN lemma.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import as_file
from typing import Dict, Optional

__all__ = ["MODES", "load_lemma_lookup", "apply_lemma_lookup"]

#: Valid values for the ``mode`` argument of :func:`apply_lemma_lookup`.
MODES = ("off", "fallback", "pos_gated", "override")


@lru_cache(maxsize=1)
def load_lemma_lookup() -> Dict[str, str]:
    """Load and cache the shipped surface-form -> lemma table (case-sensitive).

    ~1.5M entries (~42 MB JSON); loaded once and memoized for the process.
    """
    from . import la  # lazy: avoids a circular import at package init time

    with as_file(la["lemma_lookup"]) as path:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)


def _table_hit(text: str, upos: Optional[str], is_sent_start: bool,
               table: Dict[str, str]) -> Optional[str]:
    """Resolve a table candidate for ``text`` (or ``None``).

    Direct case-sensitive match first; then, for a sentence-initial
    capitalized common noun, a lowercased fallback (handles capitalization due
    to sentence position, e.g. "Arma" -> "arma"). PROPN is never lowercased
    here, to avoid lowercase-homograph collisions (e.g. Marte/martes).
    """
    if text in table:
        return table[text]
    if (
        is_sent_start
        and upos != "PROPN"
        and text[:1].isupper()
        and text.lower() in table
    ):
        return table[text.lower()]
    return None


def apply_lemma_lookup(
    text: str,
    upos: Optional[str],
    is_sent_start: bool,
    predicted_lemma: Optional[str],
    *,
    mode: str = "override",
    is_enclitic: bool = False,
    table: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """Return the lemma to use for one token after applying the lookup overlay.

    Parameters
    ----------
    text:
        The token's surface form.
    upos:
        The predicted universal POS tag (or ``None``). Only ``"PROPN"`` is
        treated specially; all other values behave identically.
    is_sent_start:
        Whether this token begins its sentence (enables the capitalized
        common-noun fallback).
    predicted_lemma:
        The lemma the model produced (may be ``None``/empty).
    mode:
        One of :data:`MODES`. See the module docstring.
    is_enclitic:
        If ``True``, the token is left untouched (enclitics are handled
        upstream by the framework's own harmonization). Frameworks that do not
        mark enclitics leave this ``False``.
    table:
        Override the lookup table (defaults to the shipped one). Lets
        experiments swap alternative dictionaries into the same call site.

    Returns
    -------
    The lemma to assign. Equal to ``predicted_lemma`` when nothing applies.
    """
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; expected one of {MODES}")
    if mode == "off" or is_enclitic or not text:
        return predicted_lemma

    tbl = table if table is not None else load_lemma_lookup()
    is_propn = upos == "PROPN"
    hit = _table_hit(text, upos, is_sent_start, tbl)

    lemma = predicted_lemma
    if mode == "fallback":
        model_punted = (not predicted_lemma) or (predicted_lemma == text)
        if hit is not None and model_punted:
            lemma = hit
    elif mode == "pos_gated":
        if hit is not None and not is_propn:
            lemma = hit
    else:  # "override" — spaCy parity
        if hit is not None:
            lemma = hit

    # Final normalization (spaCy parity): lowercase the initial of a non-PROPN
    # lemma. Catches capitalized lemmas from both the model and the table.
    if not is_propn and lemma and lemma[:1].isupper():
        lemma = lemma[0].lower() + lemma[1:]

    return lemma
