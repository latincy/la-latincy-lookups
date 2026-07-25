"""Tests for the framework-agnostic lemma-lookup overlay.

Logic tests inject a small in-memory ``table`` (fast, no 42 MB load); two
integration tests exercise the real shipped table to confirm the
homograph-exclusion invariant (present ⇒ unambiguous).
"""

import pytest

from la_latincy_lookups import MODES, apply_lemma_lookup, load_lemma_lookup

# Small fixture table for logic tests.
TBL = {
    "puellam": "puella",     # unambiguous inflected form
    "arma": "arma",          # lowercase key, for sentence-initial fallback
    "Romae": "Roma",         # for PROPN gating
    "deus": "Deus",          # capitalized lemma value, for normalization
}


# ---------------------------------------------------------------------------
# mode="off" — pure baseline
# ---------------------------------------------------------------------------

def test_off_is_noop_even_with_hit():
    assert apply_lemma_lookup("puellam", "NOUN", False, "WRONG",
                              mode="off", table=TBL) == "WRONG"


# ---------------------------------------------------------------------------
# override (spaCy parity)
# ---------------------------------------------------------------------------

def test_override_direct_hit_replaces():
    assert apply_lemma_lookup("puellam", "NOUN", False, "puellus",
                              mode="override", table=TBL) == "puella"


def test_override_miss_returns_predicted():
    assert apply_lemma_lookup("ignotum", "NOUN", False, "ignotus",
                              mode="override", table=TBL) == "ignotus"


def test_override_applies_to_propn_too():
    assert apply_lemma_lookup("Romae", "PROPN", False, "Romae",
                              mode="override", table=TBL) == "Roma"


# ---------------------------------------------------------------------------
# pos_gated — override except proper nouns
# ---------------------------------------------------------------------------

def test_pos_gated_skips_propn():
    assert apply_lemma_lookup("Romae", "PROPN", False, "Romae",
                              mode="pos_gated", table=TBL) == "Romae"


def test_pos_gated_applies_to_common_noun():
    assert apply_lemma_lookup("puellam", "NOUN", False, "puellus",
                              mode="pos_gated", table=TBL) == "puella"


# ---------------------------------------------------------------------------
# fallback — only when the model punted
# ---------------------------------------------------------------------------

def test_fallback_fills_when_identity_copy():
    # model copied the surface form -> treat as a punt, fill from table
    assert apply_lemma_lookup("puellam", "NOUN", False, "puellam",
                              mode="fallback", table=TBL) == "puella"


def test_fallback_fills_when_empty():
    assert apply_lemma_lookup("puellam", "NOUN", False, "",
                              mode="fallback", table=TBL) == "puella"
    assert apply_lemma_lookup("puellam", "NOUN", False, None,
                              mode="fallback", table=TBL) == "puella"


def test_fallback_respects_confident_model():
    # model produced a real, non-identity lemma -> leave it, even on a hit
    assert apply_lemma_lookup("puellam", "NOUN", False, "puella_model",
                              mode="fallback", table=TBL) == "puella_model"


def test_fallback_identity_copy_is_case_insensitive():
    # model copied the surface form but capitalized it (e.g. sentence-initial)
    # -> still a punt; fill from the table rather than keep the copy.
    assert apply_lemma_lookup("puellam", "NOUN", False, "Puellam",
                              mode="fallback", table=TBL) == "puella"


# ---------------------------------------------------------------------------
# default mode is "fallback" (non-regressing), not "override"
# ---------------------------------------------------------------------------

def test_default_mode_is_fallback():
    # no mode= -> confident model is respected even on a table hit (fallback),
    # NOT overridden (which is what mode="override" would do).
    assert apply_lemma_lookup("puellam", "NOUN", False, "puella_model",
                              table=TBL) == "puella_model"
    # and a punt is still filled from the table
    assert apply_lemma_lookup("puellam", "NOUN", False, "",
                              table=TBL) == "puella"


# ---------------------------------------------------------------------------
# sentence-initial capitalized-common-noun fallback
# ---------------------------------------------------------------------------

def test_sentence_initial_lowercase_fallback():
    # "Arma" not a key, but "arma" is; sentence-initial non-PROPN -> use it
    assert apply_lemma_lookup("Arma", "NOUN", True, "Arma",
                              mode="override", table=TBL) == "arma"


def test_sentence_initial_fallback_skips_propn():
    assert apply_lemma_lookup("Arma", "PROPN", True, "Arma",
                              mode="override", table=TBL) == "Arma"


def test_no_lowercase_fallback_when_not_sent_start():
    # mid-sentence capitalized form with no direct key -> no fallback
    assert apply_lemma_lookup("Arma", "NOUN", False, "Arma",
                              mode="override", table=TBL) == "arma"  # normalized only


# ---------------------------------------------------------------------------
# final normalization: lowercase non-PROPN lemma initial
# ---------------------------------------------------------------------------

def test_normalization_lowercases_non_propn():
    # table value is "Deus"; non-PROPN -> normalized to "deus"
    assert apply_lemma_lookup("deus", "NOUN", False, "deus",
                              mode="override", table=TBL) == "deus"


def test_normalization_preserves_propn_capital():
    assert apply_lemma_lookup("Roma", "PROPN", False, "Roma",
                              mode="override", table=TBL) == "Roma"


# ---------------------------------------------------------------------------
# guards
# ---------------------------------------------------------------------------

def test_enclitic_untouched():
    assert apply_lemma_lookup("puellam", "NOUN", False, "WRONG",
                              mode="override", is_enclitic=True, table=TBL) == "WRONG"


def test_empty_text_returns_predicted():
    assert apply_lemma_lookup("", "NOUN", False, "x",
                              mode="override", table=TBL) == "x"


def test_unknown_mode_raises():
    with pytest.raises(ValueError):
        apply_lemma_lookup("puellam", "NOUN", False, "x",
                           mode="bogus", table=TBL)


def test_modes_tuple_shape():
    assert MODES == ("off", "fallback", "pos_gated", "override")


# ---------------------------------------------------------------------------
# integration with the real shipped table (homograph-exclusion invariant)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_real_table_unambiguous_form_present():
    # Verified real entries in the shipped v1.1.0 table (keyed by inflected form).
    tbl = load_lemma_lookup()
    assert tbl.get("puellam") == "puella"
    assert tbl.get("amat") == "amo"
    assert apply_lemma_lookup("puellam", "NOUN", False, "WRONG",
                              mode="override") == "puella"


@pytest.mark.integration
def test_real_table_homograph_excluded():
    # "est" is a genuine homograph (esse / edo) -> excluded by construction,
    # so override leaves the model's prediction untouched.
    tbl = load_lemma_lookup()
    assert "est" not in tbl
    assert apply_lemma_lookup("est", "AUX", False, "sum",
                              mode="override") == "sum"
