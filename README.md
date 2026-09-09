# Hiver Assignment

This repository builds a reproducible customer-support agent for one brand from the Kaggle **Customer Support on Twitter** dataset.

## Current status

The selected support account is the exact observed outbound handle `SpotifyCares`. The intent taxonomy and thread-aware TF-IDF + Logistic Regression pipeline are implemented. Manual labels, evaluation metrics, response evaluation, and failure examples are intentionally **not claimed yet**.

## Quickstart

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py -m scripts.census --input data\raw --output reports\brand_census.json
```

Download `twcs.csv` from [Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter) and place it under `data/raw/` (or pass the file/directory with `--input`). The census accepts CSV and JSONL files and reports detected columns, row counts, conversation coverage, and brand candidates. It does not download data or fabricate a selection.

## Planned pipeline

1. Inspect the census and choose one brand based on observed support volume, thread coverage, response volume, and intent diversity.
2. Create a manually reviewed 150–250 row golden set from a held-out split.
3. Build intent, retrieval, response, escalation, baseline, and evaluation modules.
4. Run the reproducible quick evaluation on a configurable sample and write actual results to `reports/results.json`.

The selected account and taxonomy live in `config/brand.yaml`; definitions and real message examples are documented in `reports/intent_taxonomy.md`. Actual current metrics and limitations are recorded in [reports/results.md](reports/results.md).

Prepare held-out response outputs with retrieval leakage exclusion:

```powershell
py -m scripts.prepare_response_evaluation --limit 30
```

After real human ratings are entered in `reports/human_ratings.csv`, calculate agreement with:

```powershell
py -m evaluation.human_agreement --ratings reports/human_ratings.csv
```

The completed golden-set classifier result is written to `reports/intent_training_summary.json`. It uses a grouped 80/20 conversation split and reports actual metrics, including the majority-class effect caused by the `other_unclear` distribution. Baselines can be run with:

```powershell
py -m scripts.evaluate_baselines --labels data\golden\spotifycares_intent_golden.csv
```

## Intent annotation next step

Generate the 200-row, thread-aware annotation file:

```powershell
py -m scripts.prepare_intent_candidates --size 200
```

Manually fill the `intent` and `label_notes` columns in `data/golden/spotifycares_intent_candidates.csv` using the taxonomy document. Then train or evaluate with `scripts/train_intent.py` and `scripts/evaluate_intent.py`; both enforce conversation-level splitting and use only customer text.

For a fast provisional pass that does not modify the golden CSV, run:

```powershell
py -m scripts.review_intents --provisional
```

This writes `data/golden/spotifycares_intent_provisional_review.csv` and `reports/provisional_intent_review.md`. All 200 messages are retained with AI-suggested intent, reason, confidence, and `PENDING` human-review status. These are not hand-labelled results and must be reviewed/corrected before training.

For efficient batch human review, run:

```powershell
py -m scripts.batch_review_intents
```

The default batch size is 20. Inspect each displayed batch, then enter `a` to approve all suggestions in that batch, or `c` followed by corrections such as `2=account_access|Login is the primary issue`. Approved and corrected rows are written to `data/golden/spotifycares_intent_golden.csv` with `review_status=HUMAN_REVIEWED`; unfinished rows remain `PENDING`. The original candidate and provisional files are preserved.

The current golden file was batch-approved from provisional suggestions at the user's direction, with no recorded corrections. It is therefore not independent human ground truth; the circular keyword-baseline result is documented and must not be used as a headline claim.

For guided one-at-a-time human approval, run:

```powershell
py -m scripts.review_intents
```

Press Enter to approve a suggestion, choose `1`–`8` to correct it, `s` to skip, or `q` to save and quit. The script writes only after an approval/correction and saves progress after every decision. It never changes `message_id`, `conversation_id`, or `customer_text`.

## Repository layout

```text
data/raw/          downloaded source data (not committed)
data/processed/    reproducible derived data (not committed)
data/golden/       manually labelled evaluation data
config/            brand and intent configuration
src/               pipeline modules
scripts/            data census and future build/evaluation entry points
tests/             focused unit tests
reports/           decision log, methodology, and generated results
```

## Reproducibility and scope

All sample sizes, random seeds, paths, thresholds, and model choices will be configuration-driven. The agent will not claim to issue refunds, change accounts, access private customer data, perform transactions, or promise unsupported policies. Missing evidence should produce a conservative draft and/or escalation.

The final report will include the required baselines, leakage discussion, LLM-judge rubric, human-agreement template, failure analysis based on real outputs, and the exact section **“What is misleading about my headline number?”**. Human ratings and metrics will only be added after they are actually collected or run.
