#!/usr/bin/env python3
"""Count predefined terminology in a slide PDF, page by page.

This script does not discover terms. It takes a candidate list that has already
been compiled by the researcher and fills in slide_count and slide_dispersion.
An audit CSV records every page on which a term was found.
"""

from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import pandas as pd
from pypdf import PdfReader


REQUIRED_COLUMNS = {"term_id", "canonical_term", "selected_in_glossary"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Count candidate terms in a slide PDF.")
    parser.add_argument("--slides", required=True, type=Path)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument(
        "--output", default=Path("slide_candidates_counted.csv"), type=Path
    )
    parser.add_argument(
        "--audit", default=Path("slide_term_occurrences.csv"), type=Path
    )
    return parser.parse_args()


def normalise(text: str) -> str:
    """Normalise PDF and CSV text without attempting linguistic lemmatisation."""
    text = unicodedata.normalize("NFKC", text).casefold()
    text = re.sub(r"[\u2010-\u2015]", "-", text)
    return re.sub(r"\s+", " ", text).strip()


def term_variants(row: pd.Series) -> list[str]:
    variants = [str(row["canonical_term"])]
    aliases = row.get("aliases", "")
    if pd.notna(aliases):
        variants.extend(alias.strip() for alias in str(aliases).split("|") if alias.strip())

    # dict.fromkeys removes duplicates while preserving the order entered in CSV.
    return list(dict.fromkeys(normalise(variant) for variant in variants if variant.strip()))


def compile_term_pattern(variants: list[str]) -> re.Pattern[str]:
    alternatives = []
    for variant in sorted(variants, key=len, reverse=True):
        # Spaces and hyphens are allowed to alternate because PDF extraction often
        # breaks compounds at line endings. All other characters remain literal.
        parts = [re.escape(part) for part in re.split(r"[\s-]+", variant) if part]
        alternatives.append(r"[\s-]+".join(parts))

    joined = "|".join(alternatives)
    return re.compile(rf"(?<!\w)(?:{joined})(?!\w)")


def load_candidates(path: Path) -> pd.DataFrame:
    candidates = pd.read_csv(path)
    missing = REQUIRED_COLUMNS.difference(candidates.columns)
    if missing:
        raise ValueError(f"Candidate file is missing: {', '.join(sorted(missing))}")
    if candidates.empty:
        raise ValueError("Candidate file contains no terms")
    if candidates["term_id"].isna().any() or candidates["term_id"].duplicated().any():
        raise ValueError("term_id must be non-empty and unique")

    if "aliases" not in candidates.columns:
        candidates.insert(2, "aliases", "")
    return candidates


def extract_pages(pdf_path: Path) -> list[str]:
    reader = PdfReader(pdf_path)
    pages = [normalise(page.extract_text() or "") for page in reader.pages]
    if not any(pages):
        raise ValueError("No text could be extracted from the PDF")
    return pages


def count_terms(candidates: pd.DataFrame, pages: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    totals: list[int] = []
    dispersions: list[int] = []
    audit_rows: list[dict[str, object]] = []

    for _, row in candidates.iterrows():
        variants = term_variants(row)
        if not variants:
            raise ValueError(f"No usable form found for term_id={row['term_id']}")
        pattern = compile_term_pattern(variants)

        page_counts = []
        for page_number, page_text in enumerate(pages, start=1):
            count = len(pattern.findall(page_text))
            page_counts.append(count)
            if count:
                audit_rows.append(
                    {
                        "term_id": row["term_id"],
                        "canonical_term": row["canonical_term"],
                        "page": page_number,
                        "count": count,
                    }
                )

        totals.append(sum(page_counts))
        dispersions.append(sum(count > 0 for count in page_counts))

    counted = candidates.copy()
    counted["slide_count"] = totals
    counted["slide_dispersion"] = dispersions

    # Keep the research columns in a predictable order, but preserve any notes
    # the researcher may have added after them.
    first = [
        "term_id",
        "canonical_term",
        "aliases",
        "slide_count",
        "slide_dispersion",
        "selected_in_glossary",
    ]
    remaining = [column for column in counted.columns if column not in first]
    counted = counted[first + remaining]

    audit = pd.DataFrame(
        audit_rows, columns=["term_id", "canonical_term", "page", "count"]
    )
    return counted, audit


def main() -> None:
    args = parse_args()
    candidates = load_candidates(args.candidates)
    pages = extract_pages(args.slides)
    counted, audit = count_terms(candidates, pages)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    counted.to_csv(args.output, index=False)
    audit.to_csv(args.audit, index=False)

    print(f"Read {len(pages)} slides and {len(counted)} term families.")
    print(f"Counts: {args.output}")
    print(f"Page-level audit: {args.audit}")


if __name__ == "__main__":
    main()
