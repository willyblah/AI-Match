#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visual Design Director Core — BM25 search engine for design system generation.
4 domains: style, color, font, product.
"""

import csv
import re
from pathlib import Path
from math import log
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"
MAX_RESULTS = 3

CSV_CONFIG = {
    "style": {
        "file": "styles.csv",
        "search_cols": [
            "Style Category", "Keywords", "Best For",
            "Type", "Design_DNA"
        ],
        "output_cols": [
            "Style Category", "Type",
            "Effects & Animation",
            "Signature_Elements",
        ]
    },
    "color": {
        "file": "colors.csv",
        "search_cols": [
            "Product Type", "Keywords", "Notes"
        ],
        "output_cols": [
            "Product Type", "Primary", "On Primary",
            "Secondary",
            "Accent", "On Accent",
            "Background", "Foreground",
            "Muted", "Border",
        ]
    },
    "font": {
        "file": "fonts.csv",
        "search_cols": [
            "Font_Name_CN", "Font_Name_EN",
            "Category", "Mood_Keywords",
            "Best_For", "Best_For_CN"
        ],
        "output_cols": [
            "Font_Name_CN", "Font_Name_EN",
            "Font_Family", "Category",
            "Mood_Keywords", "Best_For", "Best_For_CN",
            "Weights", "CDN_URL",
            "CDN_URL_Template", "Usage",
            "平台", "language"
        ]
    },
    "product": {
        "file": "products.csv",
        "search_cols": [
            "Product Type", "Keywords",
            "Primary Style Recommendation"
        ],
        "output_cols": [
            "Product Type", "Keywords",
            "Primary Style Recommendation",
            "Secondary Styles",
            "Color Palette Focus",
            "Key Considerations"
        ]
    },
    "scenario": {
        "file": "scenarios.csv",
        "search_cols": ["Scenario", "Keywords"],
        "output_cols": [
            "Scenario", "Layout_Rules", "Notes",
            "Motion_Baseline", "Animation_Constraint",
        ],
    },
}


_STEM_SUFFIXES = [
    ('ational', 3), ('ation', 3),
    ('ional', 3), ('tion', 4), ('sion', 4),
    ('ment', 4), ('ness', 5),
    ('ful', 3), ('ing', 3),
    ('ous', 4), ('ive', 4), ('ity', 4),
    ('al', 4), ('ly', 4),
    ('er', 4), ('ed', 4), ('es', 4),
    ('s', 3),
]


def _stem(word):
    if len(word) <= 3:
        return word
    for suffix, min_stem in _STEM_SUFFIXES:
        if not word.endswith(suffix):
            continue
        stem = word[:-len(suffix)]
        if len(stem) < min_stem:
            continue
        if suffix in ('s', 'es') and word[-len(suffix) - 1] == 's':
            continue
        return stem
    return word


class BM25:
    """BM25 ranking algorithm for text search."""

    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.corpus = []
        self.doc_lengths = []
        self.avgdl = 0
        self.idf = {}
        self.doc_freqs = defaultdict(int)
        self.N = 0

    def tokenize(self, text):
        """Library-free tokenizer: CJK char bigrams + stemmed Latin.

        Chinese has no spaces, so split() would turn a whole phrase into one
        token and break BM25 partial matching. Character bigrams give good
        CJK recall with no dictionary/library (jieba is absent in the sandbox)
        and are far faster than jieba (no dict load). Latin words keep the
        existing stem behaviour; English search is unaffected.
        """
        text = re.sub(r'[^\w\s]', ' ', str(text).lower())
        tokens = []
        # split into CJK runs (一-鿿 = U+4E00–U+9FFF) and latin/digit runs
        for seg in re.findall(r'[一-鿿]+|[a-z0-9]+', text):
            if '一' <= seg[0] <= '鿿':
                if len(seg) == 1:
                    tokens.append(seg)
                else:
                    tokens.extend(
                        seg[i:i + 2] for i in range(len(seg) - 1)
                    )
            elif len(seg) > 2:
                tokens.append(_stem(seg))
        return tokens

    def fit(self, documents):
        """Preprocess the documents to compute IDF and average document length."""
        self.corpus = [self.tokenize(doc) for doc in documents]
        self.N = len(self.corpus)
        if self.N == 0:
            return
        self.doc_lengths = [len(doc) for doc in self.corpus]
        self.avgdl = sum(self.doc_lengths) / self.N

        for doc in self.corpus:
            seen = set()
            for word in doc:
                if word not in seen:
                    self.doc_freqs[word] += 1
                    seen.add(word)

        for word, freq in self.doc_freqs.items():
            self.idf[word] = log(
                (self.N - freq + 0.5) / (freq + 0.5) + 1
            )

    def score(self, query):
        """Compute BM25 scores for the query against all documents."""
        query_tokens = self.tokenize(query)
        scores = []

        for idx, doc in enumerate(self.corpus):
            s = 0
            doc_len = self.doc_lengths[idx]
            term_freqs = defaultdict(int)
            for word in doc:
                term_freqs[word] += 1

            for token in query_tokens:
                if token in self.idf:
                    tf = term_freqs[token]
                    idf_val = self.idf[token]
                    num = tf * (self.k1 + 1)
                    den = tf + self.k1 * (
                        1 - self.b + self.b * doc_len / self.avgdl
                    )
                    s += idf_val * num / den

            scores.append((idx, s))

        return sorted(scores, key=lambda x: x[1], reverse=True)


def _load_csv(filepath):
    """Load a data table from a real CSV or an xlsx-saved-as-.csv file.

    Excel sometimes saves the workbook in xlsx format while keeping the .csv
    name (zip magic 'PK'). Detect that and read via openpyxl so the pipeline
    never silently breaks on a re-exported data file.
    """
    with open(filepath, 'rb') as fb:
        head = fb.read(2)
    if head == b'PK':
        import io
        import openpyxl
        with open(filepath, 'rb') as fb:
            wb = openpyxl.load_workbook(
                io.BytesIO(fb.read()), read_only=True, data_only=True
            )
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [
            str(h).strip() if h is not None else "" for h in rows[0]
        ]
        out = []
        for r in rows[1:]:
            if all(c is None or str(c).strip() == "" for c in r):
                continue
            out.append({
                h: ("" if v is None else str(v))
                for h, v in zip(headers, r) if h
            })
        return out
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def _search_csv(
    filepath, search_cols, output_cols, query,
    max_results, min_score=0
):
    if not filepath.exists():
        return []

    data = _load_csv(filepath)
    documents = [
        " ".join(str(row.get(col, "")) for col in search_cols)
        for row in data
    ]

    bm25 = BM25()
    bm25.fit(documents)
    ranked = bm25.score(query)

    results = []
    for idx, score in ranked[:max_results]:
        if score > min_score:
            row = data[idx]
            results.append({
                col: row.get(col, "")
                for col in output_cols if col in row
            })

    return results


FONT_MIN_SCORE = -999


def search(query, domain=None, max_results=MAX_RESULTS):
    """Search design candidates based on the query and domain."""
    if domain is None:
        domain = "style"

    config = CSV_CONFIG.get(domain, CSV_CONFIG["style"])
    filepath = DATA_DIR / config["file"]

    if not filepath.exists():
        return {
            "error": f"File not found: {filepath}",
            "domain": domain
        }

    min_score = FONT_MIN_SCORE if domain == "font" else 0
    results = _search_csv(
        filepath,
        config["search_cols"],
        config["output_cols"],
        query,
        max_results,
        min_score
    )

    return {
        "domain": domain,
        "query": query,
        "file": config["file"],
        "count": len(results),
        "results": results
    }
