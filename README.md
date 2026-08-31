# FDA QMSR glossary coverage

This repository contains the data and small Python utilities for a corpus-based
case study of terminology preparation for remote simultaneous interpreting. The
case is an FDA webinar on the Quality Management System Regulation (QMSR).

The study asks how much of the specialised terminology used in the moderated
Q&A was covered by a glossary compiled from the presentation slides before the
Q&A was examined. It also compares that glossary with 10,000 random selections
of the same size from the complete slide-derived candidate pool.

## Research design

The primary inferential outcome is Q&A term-type coverage. Token coverage is
reported as a secondary descriptive measure. The one-sided Monte-Carlo test
uses a fixed seed and asks whether the expert glossary covers more Q&A term
families than an equally sized random selection from the slides.

The other reported measures are glossary utilisation, material ceiling and
selection efficiency. The exploratory analysis uses Spearman's rho to relate
slide dispersion to subsequent Q&A frequency. Terms absent from the slides
remain in the Q&A denominator and cannot be matched retrospectively.

The analysed section begins with “We will now transition to our moderated panel
discussion” and ends with “that will wrap up our panel discussion for today”.

## Files

- `fda_qmsr_slides.pdf` — official presentation slides;
- `transcripts/youtube_auto_transcript.txt` — working ASR transcript;
- `slide_candidates_input.csv` — frozen candidate pool and glossary selection
  before frequency counting;
- `slide_candidates_counted.csv` — final manually checked slide counts used in
  the analysis;
- `slide_term_occurrences.csv` — page-level audit of those final counts;
- `qanda_terms.csv` — independently annotated Q&A term families;
- `count_slide_terms.py` — preliminary automatic PDF counter;
- `glossary_analysis.py` — coverage measures, randomisation test, correlation
  and figures.

## Preparation of the tables

The slide candidate pool contains 98 term families. Full forms, abbreviations
and transparent orthographic variants share a stable `term_id`; nested matches
are resolved in favour of the longest expression. The 30 glossary entries are
marked in `selected_in_glossary` before the Q&A data are joined.

The PDF counter was used only as a first pass. Its page-level output was checked
against the slides. The image on slide 20 contains genuine advance material,
including the titles of upcoming webinars, but its text is absent from the PDF
text layer. Twenty-nine image-only term families were therefore entered during
manual review. Four `FDA` strings found only inside links or email addresses
were removed. The automatic `QMSR` match inside the contact address was replaced
by the visible `QMSR` label in the image, which did not change its numerical
total. A full form followed by its abbreviation counts as one occurrence of the
same term family.

Q&A terminology was annotated independently. The YouTube transcript served as
the working representation of the speech, and ASR forms were checked against
the official FDA transcript. Every row in `qanda_terms.csv` records a positive
Q&A frequency and a completed ASR check.

## Running the analysis

The required packages are listed in `requirements.txt`.

```bash
python3 -m pip install -r requirements.txt
python3 glossary_analysis.py \
  --candidates slide_candidates_counted.csv \
  --qanda qanda_terms.csv \
  --outdir analysis_output \
  --iterations 10000 \
  --seed 2026
```

The output directory contains the summary in CSV and JSON form, the joined
term-level table, all randomisation scores and two figures.

The preliminary PDF count can be reproduced separately without overwriting the
manually reviewed research data:

```bash
python3 count_slide_terms.py \
  --slides fda_qmsr_slides.pdf \
  --candidates slide_candidates_input.csv \
  --output slide_candidates_automatic.csv \
  --audit slide_term_occurrences_automatic.csv
```

The automatic files are diagnostic outputs, not substitutes for the checked
`slide_candidates_counted.csv` and `slide_term_occurrences.csv` committed here.

This is a single-event case study. It evaluates the usefulness of one set of
advance materials and one glossary; it does not measure interpreting quality,
cognitive load or interpreter performance.
