# Actual Results So Far

These values were generated from repository commands after the 200-row batch review. They are not fabricated.

## Golden intent data

- Rows: 200
- Conversation-group split: 160 train / 40 held out
- Training conversations: 158
- Held-out conversations: 40
- Distribution: `other_unclear=115`, `app_technical_issue=34`, `device_platform_compatibility=14`, `playback_audio_issue=10`, `feature_or_policy_information=9`, `account_access=7`, `playlist_library_downloads=7`, `subscription_plan_billing=4`
- Duplicate message IDs/texts: 0
- Empty/invalid labels: 0
- Validator flagged 6 multi-signal rows for audit.

## TF-IDF + Logistic Regression

- Accuracy: **0.60**
- Macro-F1: **0.09375**
- Weighted-F1: **0.45**
- The model predicted `other_unclear` for all 40 held-out examples. This is a serious class-imbalance failure, not a strong result.

## Baselines

The majority baseline achieved accuracy `0.60`, macro-F1 `0.1071428571`, and weighted-F1 `0.45`.

The keyword baseline achieved `1.0` on this split, but that result is circular: the batch-approved labels were unchanged AI suggestions produced by the same keyword logic. It must not be presented as independent evidence of classifier quality.

## Retrieval artifact

`scripts/build_spotify_cases.py` built **11,501** linked SpotifyCares customer/support cases. Each case preserves customer message ID, support message ID, conversation ID, customer text, and corresponding support response text.

## Smoke inference

For the query “My Spotify app will not play songs on my iPhone”, the actual local run returned:

- Intent: `other_unclear`
- Confidence: `0.4098081141705554`
- Decision: `ESCALATE`
- Reason: intent confidence below configured threshold
- Five traceable historical cases were retrieved, with the excluded case ID omitted.

## Bounded LLM-as-judge run

One bounded OpenRouter run made **30** judge calls using the configured `openrouter/free` model. **13** responses passed the structured rubric validation and **17** failed. Failure types were 10 invalid JSON responses, 6 schema/type validation errors, and 1 remote disconnect. The valid responses had a mean score of **2.032967032967033** across rubric dimensions. These scores cover only 13 examples and are not a headline response-quality result. Raw per-example outcomes are in `llm_judge_results.jsonl`; the aggregate is in `llm_judge_summary.json`.

Human ratings are present for all 13 examples. The first exact 13-example judge run produced 1 valid result and 12 invalid/failed results. Historical strict-schema retries raised coverage to **11/13** valid judge scores. Running `py -m evaluation.human_agreement --ratings reports\\human_ratings.csv` over the 11 matching rows produced exact agreement **0.36363636363636365** and Cohen's kappa **0.15384615384615374**; 2 rows are excluded because valid judge scores remain unavailable. This is a small, single-annotator diagnostic, not a headline response-quality metric.

## Evaluation workflows

- `scripts/prepare_response_evaluation.py` generated 30 held-out outputs with target-case retrieval exclusion.
- `scripts/prepare_human_ratings.py` generated a 13-row rating form from valid judge examples.
- `scripts/evaluate_escalation.py` is ready but rejects missing independent expected decisions.

## Interpretation

The metrics are diagnostic only. The golden set was batch-approved from provisional suggestions without recorded row-level corrections, so it is not independent human ground truth. A credible submission needs an independent manual relabeling pass or a clearly disclosed limitation and should not headline the current 0.60 accuracy.
