# RSI glossary coverage: FDA Q&A case study

I wrote this script for a small corpus-based study of terminology preparation
for remote simultaneous interpreting. The case is an FDA webinar on the
Quality Management System Regulation (QMSR).

The practical question behind the study is fairly simple: if an interpreter
receives only the official slides and prepares a glossary from them, how much
of the terminology used later in the panel discussion will that glossary
actually cover?

The script does not extract terms, correct the transcript or decide what should
go into the glossary. Those decisions are made manually. Its job starts after
the two term lists have been checked and frozen.

## What the script calculates

The main measures are:

- **type coverage:** the proportion of different Q&A term families covered by
  the glossary;
- **token coverage:** the proportion of all Q&A terminology occurrences covered
  by the glossary;
- **glossary utilisation:** how many glossary entries actually occur in the Q&A;
- **material ceiling:** how much of the Q&A terminology was present somewhere
  in the slides, whether selected for the glossary or not;
- **selection efficiency:** how much of that available terminology was captured
  by the final glossary.

The script also creates 10,000 random glossaries of the same size as the manual
glossary. This gives a simple baseline for testing whether the manual selection
covered more Q&A terminology than a random selection from the same slides.

Finally, it calculates Spearman correlations between a term's prominence in
the slides and its frequency in the Q&A. I treat this part as exploratory rather
than as the main test.

## Files in this repository

- `rsi_glossary_analysis.py` — the analysis script;
- `slide_candidates_template.csv` — all eligible term families found in the
  slides, including terms not selected for the glossary;
- `qanda_terms_template.csv` — all specialised term families found in the Q&A;
- `requirements.txt` — the Python packages used by the script.

## Order of work

The order matters because both tables should be prepared without using the
other one as a source of hints.

1. Read only the official FDA slides.
2. Complete `slide_candidates_template.csv`, mark the entries selected for the
   working glossary, and freeze the file.
3. Close the candidate file.
4. Watch or read only the Q&A and complete `qanda_terms_template.csv` without
   checking which terms occur in the slides or glossary.
5. Check uncertain automatic-transcription forms against the audio.
6. Run the script. It joins the two tables using `term_id`.

The official edited transcript is not used. The YouTube automatic transcript is
the working text, while the recording itself is treated as the final reference
when an ASR form is doubtful.

## CSV columns

### `slide_candidates_template.csv`

| Column | What to enter |
| --- | --- |
| `term_id` | A short, unique identifier shared by both files, for example `iso_13485` |
| `canonical_term` | The normalised English form of the term |
| `slide_count` | Total number of occurrences in the slides |
| `slide_dispersion` | Number of different slides containing the term |
| `selected_in_glossary` | `1` if selected for the glossary, otherwise `0` |

### `qanda_terms_template.csv`

| Column | What to enter |
| --- | --- |
| `term_id` | The same identifier used in the candidate file; create a new one if the term is absent from the slides |
| `canonical_term` | The normalised English form |
| `qanda_count` | Number of occurrences in the Q&A |
| `asr_verified` | `yes` if the form has been checked against the recording; otherwise `no` |

Full forms and abbreviations should normally share one `term_id`. The same
applies to singular/plural forms and transparent spelling variants. A term that
occurs in the Q&A but not in the slides must still be included in the Q&A file.

Do not change the header row. Replace or delete the example rows before running
the real analysis.

## Running the analysis in Terminal

The commands below are for macOS or Linux. They assume that Python 3 is already
installed.

### 1. Clone the repository and enter its folder

```bash
git clone https://github.com/vanot6/rsi-glossary-analysis.git
cd rsi-glossary-analysis
```

If the project was downloaded as a ZIP instead, open Terminal, type `cd ` with
a trailing space, drag the unzipped folder into the Terminal window, and press
Enter.

### 2. Create a separate Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

When the environment is active, `(.venv)` should appear at the start of the
Terminal prompt.

### 3. Install the required packages

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

This installation is needed only once inside the virtual environment.

### 4. Run the script

```bash
python3 rsi_glossary_analysis.py \
  --candidates slide_candidates_template.csv \
  --qanda qanda_terms_template.csv \
  --outdir analysis_output \
  --iterations 10000 \
  --seed 2026
```

On macOS, the result folder can then be opened directly from Terminal:

```bash
open analysis_output
```

To leave the virtual environment after the analysis:

```bash
deactivate
```

## Output

The `analysis_output` folder contains:

- `summary.csv` and `summary.json` — the main measures, effect sizes and
  p-values;
- `term_level_joined.csv` — the two manually prepared tables joined term by
  term, which makes the analysis easy to audit;
- `permutation_results.csv` — the results of all random glossary draws;
- `fig_randomisation.png` — the random baseline with the manual glossary result
  marked by a vertical line;
- `fig_salience_scatter.png` — slide dispersion plotted against Q&A frequency.

The script also prints the summary in Terminal, so a successful run is visible
immediately.

## Scope and limitations

This is a single-event case study. It evaluates the terminological usefulness
of one set of advance materials and one manually prepared glossary. It does not
measure interpreting quality, cognitive load or interpreter performance.

Manual term identification and normalisation remain partly subjective, and the
YouTube transcript may contain recognition errors. For that reason, the CSV
files remain part of the research record rather than disappearing behind the
final percentages and graphs.
