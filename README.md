# Glossary coverage analysis

This repository contains the scripts and data tables used for a corpus-based
case study of terminology preparation for remote simultaneous interpreting.
The material is an FDA webinar on the Quality Management System Regulation
(QMSR).

The study compares a glossary prepared from the official slides with the
terminology later used in the moderated Q&A. It asks two related questions:

1. How much of the Q&A terminology was available in the slides?
2. Did the manually selected glossary cover more terminology than an equally
   sized random selection from the same slides?

## Files

- `count_slide_terms.py` counts predefined term families in the slide PDF;
- `glossary_analysis.py` calculates coverage, runs the randomisation test and
  creates the graphs;
- `slide_candidates_template.csv` contains the slide-derived candidate list;
- `qanda_terms_template.csv` contains the terms identified in the Q&A.

The scripts do not select or extract terminology. The candidate list and the
Q&A term list are prepared manually and kept as part of the research record.

## Preparing the data

The slide candidate list is completed first, using only the official slides.
`aliases` contains alternative forms separated by `|`; full forms, acronyms and
transparent variants share one `term_id`. `selected_in_glossary` is `1` for an
entry included in the working glossary and `0` otherwise.

`count_slide_terms.py` then reads the PDF page by page. Matching is
case-insensitive and treats spaces and hyphens flexibly, which helps with PDF
line breaks. It writes both the total frequency (`slide_count`) and the number
of slides containing the term (`slide_dispersion`). A separate audit file lists
the positive counts by page, so questionable matches can be checked manually.

```bash
python count_slide_terms.py \
  --slides fda_qmsr_slides.pdf \
  --candidates slide_candidates_template.csv \
  --output slide_candidates_counted.csv \
  --audit slide_term_occurrences.csv
```

After the slide list has been frozen, the Q&A is annotated without consulting
it. The YouTube automatic transcript is used as a working text, but doubtful
forms are checked against the recording. The official edited transcript is not
used.

## Running the analysis

The project uses Python 3 and the packages listed in `requirements.txt`.

```bash
pip install -r requirements.txt

python glossary_analysis.py \
  --candidates slide_candidates_counted.csv \
  --qanda qanda_terms_template.csv \
  --outdir analysis_output \
  --iterations 10000 \
  --seed 2026
```

The main outputs are type and token coverage, glossary utilisation, material
ceiling and selection efficiency. The randomisation test compares the observed
glossary with 10,000 random glossaries of the same size. The script also reports
Spearman correlations between term prominence in the slides and frequency in
the Q&A.

`term_level_joined.csv` is saved together with the summary and graphs. I kept
this table because it makes it possible to trace a surprising result back to
the individual term rather than relying only on the final percentages.

This is a single-event case study. It evaluates one set of advance materials
and one glossary; it does not measure interpreting quality or cognitive load.
