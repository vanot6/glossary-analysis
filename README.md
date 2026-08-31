# RSI glossary coverage analysis

This small utility evaluates a **manually compiled, frozen glossary** against a
**manually annotated Q&A transcript**. It does not extract terms and does not
change the glossary after the Q&A has been inspected.

## Research logic

The script reports:

- Q&A term-type coverage;
- frequency-weighted Q&A token coverage;
- glossary utilisation;
- the maximum coverage permitted by the supplied slides (material ceiling);
- selection efficiency within that ceiling;
- a one-sided Monte-Carlo randomisation test comparing the expert glossary with
  10,000 equally sized random glossaries drawn from the same slide candidate pool;
- exploratory Spearman correlations between slide prominence and Q&A frequency.

The randomisation null hypothesis is: **expert selection has no greater Q&A
coverage than a random selection of the same number of eligible slide-derived
terms**.

## Input files

Use the two included templates. `term_id` must be a stable identifier shared by
both tables. Full forms, acronyms, singular/plural forms and spelling variants
should be assigned to the same `term_id` according to a rule fixed before the
analysis.

`slide_candidates.csv` contains every eligible slide-derived term family, not
only the selected glossary entries. Set `selected_in_glossary` to 1 for the
frozen expert glossary and 0 otherwise.

`qanda_terms.csv` contains every specialised term family occurring in the Q&A,
including terms absent from the slides. Check uncertain ASR forms against the
audio and document corrections separately; do not use an edited official
transcript as the reference.

## Installation and execution

```bash
python -m pip install -r requirements.txt
python rsi_glossary_analysis.py \
  --candidates slide_candidates_template.csv \
  --qanda qanda_terms_template.csv \
  --outdir analysis_output \
  --iterations 10000 \
  --seed 2026
```

Replace the example rows in the templates before analysing the study data.

## Outputs

- `summary.csv` and `summary.json`: overall metrics, effect sizes and p-values;
- `term_level_joined.csv`: auditable joined data;
- `permutation_results.csv`: all randomisation scores;
- `fig_randomisation.png`: null distributions and observed scores;
- `fig_salience_scatter.png`: slide dispersion versus Q&A frequency.

This is a single-event case study. The results describe this FDA webinar and do
not establish effects on interpreting quality, cognitive load or all RSI events.
