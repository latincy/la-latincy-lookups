#!/usr/bin/env python3
"""Audit a UD treebank's lemma harmonization using the unambiguous lookup table.

The la-latincy-lookups table excludes homographs by construction, so any surface
form present in it is asserted to map to exactly ONE lemma. Where the treebank
assigns 2+ distinct lemmas to such a form, that is a strong candidate for a
harmonization defect (null/garbage lemma, capitalization drift, annotation error,
or an unsettled citation-form convention) — NOT a genuine homograph.

This is a free, high-precision QA signal for the latincy-treebanks harmonization
program. It also surfaces reciprocal table bugs (a form whose single table lemma
is degenerate, e.g. 'h' / 'qu').

Emits a TSV sorted so the most actionable rows come first (table lemma NOT among
the gold lemmas => outright disagreement), with a coarse flag per row.

Usage:
    python scripts/audit_treebank_consistency.py \
        --conllu /path/to/UD_Latin-LatinCy/la_latincy-ud-*.conllu \
        --out handoff/treebank-lemma-inconsistencies.tsv
"""

import argparse
import glob
import sys
from collections import defaultdict
from pathlib import Path

from la_latincy_lookups import load_lemma_lookup


def collect(paths):
    form2lem = defaultdict(set)
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("#") or not line.strip():
                    continue
                f = line.rstrip("\n").split("\t")
                if len(f) != 10 or "-" in f[0] or "." in f[0]:
                    continue
                form2lem[f[1]].add(f[2])
    return form2lem


def flag(form, gold_lemmas, table_lemma):
    if "_" in gold_lemmas:
        return "null_lemma"                       # missing annotation
    if len(table_lemma) <= 2 and any(len(g) >= 3 for g in gold_lemmas):
        return "table_bug(degenerate)"            # reciprocal: table side is wrong
    low = {g.lower() for g in gold_lemmas}
    if len(low) < len(gold_lemmas):
        return "capitalization"                   # differ only by case
    if table_lemma not in gold_lemmas:
        return "disagree(table not in gold)"      # strongest signal
    return "convention(citation-form)"            # e.g. incertum/incertus


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--conllu", nargs="+", required=True,
                    help="gold CoNLL-U file(s) or globs")
    ap.add_argument("--out", type=Path,
                    default=Path("handoff/treebank-lemma-inconsistencies.tsv"))
    args = ap.parse_args()

    paths = [p for g in args.conllu for p in glob.glob(g)]
    if not paths:
        sys.exit(f"no files matched: {args.conllu}")
    print(f"scanning {len(paths)} file(s)...", file=sys.stderr)

    form2lem = collect(paths)
    tbl = load_lemma_lookup()

    rows = []
    for form, lemmas in form2lem.items():
        if len(lemmas) < 2 or form not in tbl:
            continue
        rows.append((form, sorted(lemmas), tbl[form], flag(form, lemmas, tbl[form])))

    # Order: outright disagreements and table bugs first, then by breadth of gold spread.
    order = {"disagree(table not in gold)": 0, "table_bug(degenerate)": 1,
             "null_lemma": 2, "capitalization": 3, "convention(citation-form)": 4}
    rows.sort(key=lambda r: (order.get(r[3], 9), -len(r[1]), r[0]))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("form\tn_gold_lemmas\tgold_lemmas\ttable_lemma\tflag\n")
        for form, lemmas, tl, fl in rows:
            fh.write(f"{form}\t{len(lemmas)}\t{'|'.join(lemmas)}\t{tl}\t{fl}\n")

    from collections import Counter
    dist = Counter(r[3] for r in rows)
    print(f"\ndistinct forms scanned: {len(form2lem)}")
    print(f"candidate inconsistencies (>=2 gold lemmas, form in unambiguous table): {len(rows)}")
    for fl, ct in dist.most_common():
        print(f"  {fl:<32} {ct:>6}")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
