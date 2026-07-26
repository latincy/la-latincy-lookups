"""Regression tests for the irregular-verb suppletive-form fix (v1.2.2).

Spot-checks the real shipped table against the exact defect documented in
.claude/reports/irregular-verb-coverage-gap.md: `est`, `sum`, `es`, `esse` --
the four highest-frequency forms of the most common verb in Latin -- were all
missing or wrongly attached to the wrong lemma. The fix (curated exception
layer in latincy-words, see irregular-verb-fix-scope-note.md) restores the
forms that are NOT genuine classical homographs, while leaving the genuine
homographs (est/edo, etc.) correctly excluded -- these are two distinct
categories and must not be conflated. Mirrors test_provenance.py's style.
"""

import pytest

from la_latincy_lookups import load_lemma_lookup


@pytest.mark.integration
def test_curated_irregular_verb_forms_present():
    """Forms confirmed NOT to be genuine homographs now resolve unambiguously."""
    tbl = load_lemma_lookup()
    cases = {
        "sum": "sum",
        "sumus": "sum",
        "posse": "possum",
        "uult": "uolo",
        "uultis": "uolo",
        "iit": "eo",
        "iimus": "eo",
        "ierunt": "eo",
        "iens": "eo",
    }
    for form, expected_lemma in cases.items():
        assert tbl.get(form) == expected_lemma, (
            f"'{form}' should resolve to '{expected_lemma}', got {tbl.get(form)!r}"
        )


@pytest.mark.integration
def test_genuine_homographs_still_correctly_excluded():
    """Genuine classical homographs are NOT force-resolved and remain excluded.

    This is the flip side of test_curated_irregular_verb_forms_present: the fix
    must not overturn the homograph-exclusion policy for forms that collide with
    a real, independently attested, common Latin word (edo "to eat", the pronoun
    is/ea/id, ferio "to strike", ferrum "iron", latus "side/wide").
    """
    tbl = load_lemma_lookup()
    for form in ["est", "es", "estis", "esse", "essem",
                 "is", "eam", "eas",
                 "ferimus", "ferri", "latum"]:
        assert form not in tbl, (
            f"'{form}' is a genuine homograph and must remain excluded from "
            f"the lookup, but resolved to {tbl.get(form)!r}"
        )
