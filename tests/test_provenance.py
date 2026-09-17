"""Regression tests pinning the vendored lemma_lookup table to its known-good
source (latincy-words v3.10.1 / commit a46f6c1, UD fixed-self-lemma fix).

These guard against silently re-vendoring a stale or truncated table: if the
entry count or any of the assimilation-fold spot checks drift, either the
source table changed intentionally (update PROVENANCE.json + this test) or
something went wrong in the re-vendor step.
"""

import json

import pytest

from la_latincy_lookups import load_lemma_lookup

PROVENANCE_PATH = "la_latincy_lookups/data/PROVENANCE.json"


def _load_provenance():
    with open(PROVENANCE_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def test_provenance_file_present_and_well_formed():
    prov = _load_provenance()
    assert prov["source_repo"] == "https://github.com/latincy/latincy-words"
    assert prov["source_commit"] == "a46f6c1ba026b963ea11c8da43cdf094168fa562"
    assert prov["entry_count"] == 1502997


@pytest.mark.integration
def test_real_table_entry_count_pinned():
    # Pins the shipped table to the latincy-words v3.10.1 build.
    # Was 1,502,867 (v1.2.0, stale); 1,502,959 (v1.2.1, harmonize-citation-conventions);
    # 1,502,968 (v1.2.2, +9 curated irregular-verb overrides);
    # now 1,502,997 (v1.2.3, +30 UD fixed-self-lemma recoveries, -1 unnormalized v-key).
    tbl = load_lemma_lookup()
    assert len(tbl) == 1502997


@pytest.mark.integration
@pytest.mark.parametrize(
    "surface_form,expected_lemma",
    [
        # Bare-stem pronoun relabel (pre-existing, still holds): haec -> hic.
        ("haec", "hic"),
        # Prefix-assimilation folds newly merged in harmonize-citation-conventions.
        ("adfrio", "affrio"),
        ("subplico", "supplico"),
        ("obfendo", "offendo"),
    ],
)
def test_real_table_assimilation_folds(surface_form, expected_lemma):
    tbl = load_lemma_lookup()
    assert tbl.get(surface_form) == expected_lemma


@pytest.mark.integration
@pytest.mark.parametrize(
    "surface_form,expected_lemma",
    [
        # v1.2.3: forms evicted by fake UD `fixed` self-lemmas, now recovered.
        ("nulli", "nullus"),
        ("nulla", "nullus"),
        ("facere", "facio"),
        ("re", "res"),
        ("modum", "modus"),
        ("nouembris", "nouember"),
    ],
)
def test_real_table_fixed_self_lemma_recoveries(surface_form, expected_lemma):
    tbl = load_lemma_lookup()
    assert tbl.get(surface_form) == expected_lemma


@pytest.mark.integration
@pytest.mark.parametrize("surface_form", ["milia", "uenirent", "da", "des", "hercule"])
def test_real_table_genuine_self_lemma_homographs_still_excluded(surface_form):
    # Still ambiguous among real lemmas (milia, uenirent) or genuine headwords
    # (da, des, hercule): must NOT have been swept up by the v1.2.3 fix.
    tbl = load_lemma_lookup()
    assert surface_form not in tbl
