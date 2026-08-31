# FDA QMSR glossary coverage

This repo contains the data and Python scripts used for a small corpus-based case study on terminology preparation for remote simultaneous interpreting.

The source event is an FDA webinar on the Quality Management System Regulation (QMSR). I wanted to find out how much of the terminology used during the moderated Q&A could have been prepared in advance using only the presentation slides.

I also compared my 30-term glossary with 10,000 random selections of 30 terms from the same slide-derived candidate pool.

## What the analysis does

The main measure is **term-type coverage**: the percentage of Q&A term families covered by the glossary. Token coverage is included as an additional descriptive measure.

The Monte Carlo test checks whether the manually selected glossary covers more Q&A term families than a random selection of the same size. The random seed is fixed, so the results can be reproduced.

The script also calculates:

- glossary utilisation;
- the maximum coverage possible using the slides alone;
- selection efficiency;
- the relationship between a term’s distribution across the slides and its later frequency in the Q&A, using Spearman’s rho.

Terms that appeared in the Q&A but not in the slides remain in the denominator. In other words, the analysis does not pretend that terms unavailable during preparation could somehow have been selected retrospectively.

The Q&A section starts with:

> We will now transition to our moderated panel discussion

and ends with:

> that will wrap up our panel discussion for today

## Repository contents

- `fda_qmsr_slides.pdf` — official FDA presentation slides
- `transcripts/youtube_auto_transcript.txt` — working YouTube ASR transcript
- `slide_candidates_input.csv` — frozen slide-derived candidate pool, including the original glossary selection
- `slide_candidates_counted.csv` — manually checked slide frequencies used in the final analysis
- `slide_term_occurrences.csv` — page-level audit of the checked slide counts
- `qanda_terms.csv` — independently annotated Q&A term families
- `count_slide_terms.py` — preliminary automatic PDF counter
- `glossary_analysis.py` — main analysis script

## How the data were prepared

The candidate pool contains 98 term families. Full forms, abbreviations and straightforward spelling variants are grouped under the same stable `term_id`. Where expressions overlap, the longest valid match takes priority.

The 30 terms included in the glossary were marked in `selected_in_glossary` before the Q&A data were added.

The automatic PDF count was only a starting point. I checked its page-level results manually against the slides because the PDF text layer was incomplete.

Slide 20 was the main issue. It contains an image with real advance material, including the titles of upcoming webinars, but none of that text is available in the PDF text layer. I therefore added 29 image-only term families manually.

I also removed four occurrences of `FDA` that appeared only inside hyperlinks or email addresses. One automatic `QMSR` match from the contact address was replaced with the visible `QMSR` label in the image. This correction did not change the total count.

A full term followed immediately by its abbreviation is counted as one occurrence of the same term family.

The Q&A terminology was annotated separately. I used the YouTube ASR transcript as the working version of the spoken text and checked questionable ASR forms against the official FDA transcript. Every entry in `qanda_terms.csv` has a positive Q&A frequency and has been checked against the transcript.

## Running the analysis

Install the required packages:

```bash
python3 -m pip install -r requirements.txt
```

Then run:

```bash
python3 glossary_analysis.py \
  --candidates slide_candidates_counted.csv \
  --qanda qanda_terms.csv \
  --outdir analysis_output \
  --iterations 10000 \
  --seed 2026
```

The output directory will contain:

- summaries in CSV and JSON format;
- the joined term-level dataset;
- all 10,000 randomisation scores;
- two figures.

## Reproducing the automatic slide count

The preliminary PDF count can be run separately:

```bash
python3 count_slide_terms.py \
  --slides fda_qmsr_slides.pdf \
  --candidates slide_candidates_input.csv \
  --output slide_candidates_automatic.csv \
  --audit slide_term_occurrences_automatic.csv
```

This creates new diagnostic files and does not overwrite the manually checked data.

The automatic outputs should not be used instead of `slide_candidates_counted.csv` and `slide_term_occurrences.csv`. The checked files are the ones used for the reported results.

## Scope

This is a case study of one webinar, one set of advance materials and one glossary. It looks at terminology coverage only. It does not attempt to measure interpreting quality, cognitive load or the interpreter’s overall performance.
