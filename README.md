# la-latincy-lookups

Latin lookup tables for [LatinCy](https://github.com/diyclassics/latincy) spaCy pipelines.

When installed in the same environment as spaCy, this package registers Latin lookup data via spaCy's entry point system, making it available to any `la` pipeline that uses lookup-based lemmatization.

## Contents

| Table | Entries | Sources |
|-------|---------|---------|
| `lemma_lookup` | 948,252 | CLTK Morpheus, Kaikki Wiktionary, UD treebanks |

## Installation

```bash
pip install git+https://github.com/latincy/la-latincy-lookups.git
```

**Note:** The lookup JSON file is tracked with [Git LFS](https://git-lfs.github.com/). Make sure Git LFS is installed before cloning.

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

MIT
