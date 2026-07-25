# la-latincy-lookups

Latin lookup tables for [LatinCy](https://github.com/diyclassics/latincy) spaCy pipelines.

When installed in the same environment as spaCy, this package registers Latin lookup data via spaCy's entry point system, making it available to any `la` pipeline that uses lookup-based lemmatization.

## Contents

| Table | Entries | Sources |
|-------|---------|---------|
| `lemma_lookup` | 1,502,867 | Wiktionary (Kaikki), UD treebanks |

## Installation

```bash
pip install la-latincy-lookups
```

**Note:** For development, the lookup JSON file in the source repo is tracked with [Git LFS](https://git-lfs.github.com/). Make sure Git LFS is installed before cloning.

## Usage

The lookup table is registered automatically via spaCy's `spacy_lookups` entry point. Any `la` pipeline with a `lookup` lemmatizer will use it:

```python
from spacy.lookups import load_lookups

lookups = load_lookups(lang="la", tables=["lemma_lookup"])
table = lookups.get_table("lemma_lookup")
```

## Requirements

- Python >= 3.9
- spaCy >= 3.8.0, < 4.0.0

## License

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). This package is a dataset, so it carries a content license rather than a software license. The lookup data is derived from Wiktionary (CC BY-SA 3.0) and Universal Dependencies treebanks (CC BY-NC-SA 3.0); the non-commercial terms of UD PROIEL and ITTB require the NC clause. See [latincy-words](https://github.com/latincy/latincy-words) for full provenance and citations.
