#!/usr/bin/env python3
"""Analyse a manually compiled interpreting glossary against an annotated Q&A.

Term selection and transcript checking stay outside the script. This file only
handles the repeatable part: joining the two frozen CSV files, calculating the
coverage measures, running the randomisation test and drawing the figures.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr


CANDIDATE_REQUIRED = {
    "term_id",
    "canonical_term",
    "slide_count",
    "slide_dispersion",
    "selected_in_glossary",
}
QANDA_REQUIRED = {
    "term_id",
    "canonical_term",
    "qanda_count",
    "asr_verified",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate an expert glossary against Q&A terminology."
    )
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--qanda", required=True, type=Path)
    parser.add_argument("--outdir", default=Path("analysis_output"), type=Path)
    parser.add_argument("--iterations", default=10_000, type=int)
    parser.add_argument("--seed", default=2026, type=int)
    return parser.parse_args()


def require_columns(df: pd.DataFrame, required: set[str], label: str) -> None:
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"{label} is missing columns: {', '.join(sorted(missing))}")


def load_and_validate(candidates_path: Path, qanda_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Most mistakes in this project are likely to be small spreadsheet errors.
    # Failing early here is much nicer than producing a plausible-looking graph
    # from a broken input file.
    candidates = pd.read_csv(candidates_path)
    qanda = pd.read_csv(qanda_path)
    require_columns(candidates, CANDIDATE_REQUIRED, "Candidate table")
    require_columns(qanda, QANDA_REQUIRED, "Q&A table")

    for label, df in (("Candidate table", candidates), ("Q&A table", qanda)):
        if df["term_id"].isna().any() or df["term_id"].duplicated().any():
            raise ValueError(f"{label}: term_id must be non-empty and unique")

    candidates["slide_count"] = pd.to_numeric(candidates["slide_count"], errors="raise")
    candidates["slide_dispersion"] = pd.to_numeric(
        candidates["slide_dispersion"], errors="raise"
    )
    selected = pd.to_numeric(candidates["selected_in_glossary"], errors="raise")
    qanda["qanda_count"] = pd.to_numeric(qanda["qanda_count"], errors="raise")

    if selected.isna().any() or not selected.isin([0, 1]).all():
        raise ValueError("selected_in_glossary must contain only 0 or 1")
    candidates["selected_in_glossary"] = selected.astype(int)
    if candidates[["slide_count", "slide_dispersion"]].isna().any().any():
        raise ValueError("slide_count and slide_dispersion must not be blank")
    if (candidates[["slide_count", "slide_dispersion"]] < 0).any().any():
        raise ValueError("Slide counts cannot be negative")
    if qanda["qanda_count"].isna().any() or (qanda["qanda_count"] <= 0).any():
        raise ValueError("Every Q&A row must have a positive qanda_count")
    if candidates["selected_in_glossary"].sum() == 0:
        raise ValueError("At least one candidate must be selected in the glossary")

    return candidates, qanda


def join_tables(candidates: pd.DataFrame, qanda: pd.DataFrame) -> pd.DataFrame:
    # The outer join is intentional. A Q&A term that never appeared in the
    # slides still belongs in the denominator and must not quietly disappear.
    joined = candidates.merge(
        qanda,
        on="term_id",
        how="outer",
        suffixes=("_slides", "_qanda"),
        indicator=True,
    )
    joined["canonical_term"] = joined["canonical_term_qanda"].fillna(
        joined["canonical_term_slides"]
    )
    joined["slide_count"] = joined["slide_count"].fillna(0)
    joined["slide_dispersion"] = joined["slide_dispersion"].fillna(0)
    joined["selected_in_glossary"] = joined["selected_in_glossary"].fillna(0).astype(int)
    joined["qanda_count"] = joined["qanda_count"].fillna(0)
    joined["present_in_slides"] = joined["_merge"].isin(["both", "left_only"])
    joined["present_in_qanda"] = joined["qanda_count"] > 0
    joined["covered"] = joined["present_in_qanda"] & joined["selected_in_glossary"].eq(1)
    return joined


def safe_ratio(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else float("nan")


def calculate_metrics(joined: pd.DataFrame) -> dict[str, float | int]:
    # Keep the intermediate groups named. This makes the formulas below easier
    # to compare with the definitions used in the case-study methodology.
    q = joined[joined["present_in_qanda"]]
    glossary = joined[joined["selected_in_glossary"].eq(1)]
    q_from_slides = q[q["present_in_slides"]]
    covered = q[q["covered"]]

    return {
        "qanda_term_types": int(len(q)),
        "qanda_term_tokens": int(q["qanda_count"].sum()),
        "candidate_pool_size": int(joined["present_in_slides"].sum()),
        "glossary_size": int(len(glossary)),
        "covered_qanda_types": int(len(covered)),
        "covered_qanda_tokens": int(covered["qanda_count"].sum()),
        "type_coverage": safe_ratio(len(covered), len(q)),
        "token_coverage": safe_ratio(covered["qanda_count"].sum(), q["qanda_count"].sum()),
        "glossary_utilisation": safe_ratio(
            glossary["present_in_qanda"].sum(), len(glossary)
        ),
        "material_ceiling": safe_ratio(len(q_from_slides), len(q)),
        "selection_efficiency": safe_ratio(len(covered), len(q_from_slides)),
    }


def randomisation_test(
    candidates: pd.DataFrame,
    qanda_counts: pd.Series,
    iterations: int,
    seed: int,
) -> tuple[pd.DataFrame, dict[str, float]]:
    if iterations < 1000:
        raise ValueError("Use at least 1,000 iterations")

    pool = candidates["term_id"].to_numpy()
    n = int(candidates["selected_in_glossary"].sum())
    if n > len(pool):
        raise ValueError("Glossary size cannot exceed the candidate pool")

    counts = qanda_counts.reindex(pool, fill_value=0).to_numpy(dtype=float)
    total_types = int((qanda_counts > 0).sum())
    selected = candidates["selected_in_glossary"].eq(1).to_numpy()
    observed_type = safe_ratio(((counts > 0) & selected).sum(), total_types)

    # A fixed seed makes the 10,000 draws reproducible. Someone rerunning the
    # repository should get exactly the same baseline and p-value.
    rng = np.random.default_rng(seed)
    type_scores = np.empty(iterations)
    for i in range(iterations):
        sample_idx = rng.choice(len(pool), size=n, replace=False)
        sample_counts = counts[sample_idx]
        type_scores[i] = safe_ratio((sample_counts > 0).sum(), total_types)

    results = pd.DataFrame(
        {
            "iteration": np.arange(1, iterations + 1),
            "type_coverage": type_scores,
        }
    )
    # The +1 correction prevents a Monte-Carlo p-value of exactly zero and keeps
    # the simulated estimate conservative for a finite number of draws.
    stats = {
        "observed_type_coverage": observed_type,
        "random_mean_type_coverage": float(type_scores.mean()),
        "type_coverage_advantage": float(observed_type - type_scores.mean()),
        "type_coverage_p_one_sided": float(
            (1 + np.count_nonzero(type_scores >= observed_type)) / (iterations + 1)
        ),
        "type_coverage_percentile_rank": float(
            100
            * (
                np.count_nonzero(type_scores < observed_type)
                + 0.5 * np.count_nonzero(type_scores == observed_type)
            )
            / iterations
        ),
    }
    return results, stats


def salience_correlations(candidates: pd.DataFrame, qanda_counts: pd.Series) -> dict[str, float]:
    # Counts are skewed and tied, with many candidates never used in the Q&A.
    # Spearman's rho is therefore a better fit here than Pearson correlation.
    c = candidates.copy()
    c["qanda_count"] = c["term_id"].map(qanda_counts).fillna(0)
    rho, p = spearmanr(c["slide_dispersion"], c["qanda_count"])
    return {
        "spearman_slide_dispersion_rho": float(rho),
        "spearman_slide_dispersion_p_two_sided": float(p),
    }


def plot_randomisation(
    permutations: pd.DataFrame, stats: dict[str, float], outdir: Path
) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(permutations["type_coverage"], bins=30, color="#5B8FF9", edgecolor="white")
    ax.axvline(
        stats["observed_type_coverage"],
        color="#C33C54",
        linewidth=2.5,
        label="Expert glossary",
    )
    ax.set_title("Randomisation baseline: Q&A type coverage")
    ax.set_xlabel("Type coverage")
    ax.set_ylabel("Random glossaries")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(outdir / "fig_randomisation.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_salience(candidates: pd.DataFrame, qanda_counts: pd.Series, outdir: Path) -> None:
    c = candidates.copy()
    c["qanda_count"] = c["term_id"].map(qanda_counts).fillna(0)
    selected = c["selected_in_glossary"].eq(1)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(
        c.loc[~selected, "slide_dispersion"],
        c.loc[~selected, "qanda_count"],
        alpha=0.55,
        label="Not selected",
    )
    ax.scatter(
        c.loc[selected, "slide_dispersion"],
        c.loc[selected, "qanda_count"],
        alpha=0.8,
        label="Expert glossary",
    )
    ax.set_xlabel("Slide dispersion (number of slides)")
    ax.set_ylabel("Q&A occurrences")
    ax.set_title("Slide prominence and subsequent Q&A frequency")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(outdir / "fig_salience_scatter.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    candidates, qanda = load_and_validate(args.candidates, args.qanda)
    joined = join_tables(candidates, qanda)
    metrics = calculate_metrics(joined)
    qanda_counts = qanda.set_index("term_id")["qanda_count"]
    permutations, permutation_stats = randomisation_test(
        candidates, qanda_counts, args.iterations, args.seed
    )
    correlations = salience_correlations(candidates, qanda_counts)
    summary = {**metrics, **permutation_stats, **correlations}

    # Save the joined term table as well as the summary. This is useful when a
    # percentage looks surprising and I need to trace it back to individual terms.
    joined.to_csv(args.outdir / "term_level_joined.csv", index=False)
    permutations.to_csv(args.outdir / "permutation_results.csv", index=False)
    pd.DataFrame([summary]).to_csv(args.outdir / "summary.csv", index=False)
    (args.outdir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    plot_randomisation(permutations, permutation_stats, args.outdir)
    plot_salience(candidates, qanda_counts, args.outdir)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
