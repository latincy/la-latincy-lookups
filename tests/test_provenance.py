"""Regression tests pinning the vendored lemma_lookup table to its known-good
source (latincy-words commit 8b0b641, post harmonize-citation-conventions merge).

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
    assert prov["source_commit"] == "8b0b64161e025699d3e0d69748aa4165876e6cd6"
    assert prov["entry_count"] == 1502959


@pytest.mark.integration
def test_real_table_entry_count_pinned():
    # Pins the shipped table to the post-harmonization latincy-words build.
    # Was 1,502,867 (v1.2.0, stale); now 1,502,959 (v1.2.1, re-vendored).
    tbl = load_lemma_lookup()
    assert len(tbl) == 1502959


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
