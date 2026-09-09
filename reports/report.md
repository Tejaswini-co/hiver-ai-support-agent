# SpotifyCares Support Agent Report

## Executive summary

This project builds a lightweight customer-support agent for the exact TWCS support handle `SpotifyCares`. It classifies incoming customer text, retrieves linked historical customer/support cases, drafts an evidence-constrained reply, and applies a conservative escalation rule. The local pipeline is runnable without an API key.

## Problem framing and scope

Good means identifying the primary support problem, retrieving relevant historical handling, avoiding unsupported promises, and escalating uncertain or sensitive requests. The system does not issue refunds, change accounts, access private data, perform transactions, or claim that an action was completed.

## Data and selection

The full export contains 2,811,774 rows. It has no explicit brand column. `inbound=False` rows expose support handles in `author_id`, and `in_response_to_tweet_id` links messages. `SpotifyCares` was selected from actual data because it has 15,096 linked customer messages, 8,723 customer accounts, 11,938 linked company replies, and 11,501 customer messages with direct replies. Details are in [brand_selection.md](brand_selection.md).

## Taxonomy and architecture

The eight-intent taxonomy is `playback_audio_issue`, `app_technical_issue`, `account_access`, `subscription_plan_billing`, `playlist_library_downloads`, `device_platform_compatibility`, `feature_or_policy_information`, and `other_unclear`. Definitions and real examples are in [intent_taxonomy.md](intent_taxonomy.md).

Pipeline: customer text -> TF-IDF/logistic intent classifier -> TF-IDF historical retrieval -> evidence-constrained draft -> escalation policy -> structured output.

## Leakage controls

Intent data is split with `GroupShuffleSplit` by `conversation_id`. Classifier features contain customer text only, never future company replies. Retrieval accepts explicit excluded case IDs; evaluation retrieval must exclude the target conversation and held-out evidence.

## Results

The 200-row AI-assisted review artifact has 160 train and 40 held-out examples. It is **not an independently hand-labelled golden set**: all rows were batch-approved from AI suggestions and no independent corrections were recorded. TF-IDF + Logistic Regression achieved accuracy **0.60**, macro-F1 **0.09375**, and weighted-F1 **0.45**. It predicted `other_unclear` for all held-out rows. The majority baseline achieved accuracy 0.60 and macro-F1 0.1071. The keyword baseline scored 1.0, but labels were batch-approved from the same heuristic suggestions, so this result is circular and not independent evidence. Full values are in [results.md](results.md).

## Retrieval and response

The build script produced 11,501 linked cases with customer text, support response, message IDs, and conversation IDs. Drafts quote historical support language and avoid claiming actions. The smoke run retrieved five traceable cases and escalated a low-confidence query.

The command `py -m scripts.prepare_response_evaluation --limit 30` generated 30 held-out agent outputs with the target case excluded from retrieval.

## Evaluation status

Intent metrics and baselines are computed. A bounded OpenRouter judge run made 30 calls: 13 valid structured results and 17 failures. A second exact 13-example run made 1 valid result and 12 failures; historical strict-schema retries raised valid exact coverage to **11/13**. Human ratings are present for all 13 examples. The calculated agreement over the 11 matching scores is exact agreement **0.3636** and Cohen's kappa **0.1538**; two examples (`315129` and `1691143`) remain excluded because no valid judge score is stored. This small, single-annotator comparison is diagnostic only, not a general response-quality claim. Exact matching response material is in `human_review_outputs.jsonl`, and ratings are in `human_ratings.csv`. Escalation quality requires independent escalation labels not currently in the golden file; its evaluator rejects missing labels.

## Failure analysis

Observed failures include majority-class collapse and circular keyword evaluation. Five response-quality failure examples from the stored human-reviewed outputs are documented in [failure_analysis.md](failure_analysis.md). They are qualitative observed examples, not statistically validated failure rates.

## What is misleading about my headline number?

The 0.60 accuracy is misleading if presented alone. The dataset is imbalanced, the held-out set has only 40 examples, six classes have tiny support, and the model achieves that accuracy by predicting `other_unclear` for every case. The labels were batch-approved from AI suggestions rather than independently re-annotated, so they are not strong ground truth. Accuracy also does not measure grounded reply quality, safe escalation, or customer satisfaction. Escalation mistakes can be more costly than ordinary intent mistakes.

## What I would do with one more week

Independently relabel the golden set, increase difficult/rare examples, calibrate confidence, add conversation-level hybrid retrieval, add explicit escalation labels, run a real LLM judge on stored outputs, collect 30-50 human ratings, calculate weighted agreement, and add regression tests for leakage, unsupported claims, and retrieval exclusions.

## Limitations

The 200 intent labels are AI-assisted batch approvals rather than independent hand labels, so intent and baseline metrics are diagnostic only. The response agreement calculation covers 11 examples from one annotator and excludes two examples without valid judge outputs; it is not a population-quality estimate. The five response failures are real qualitative examples, not measured failure rates. Independent escalation labels are still absent, so escalation quality cannot be scored.

## Decision log and reproducibility

Non-obvious choices are recorded in [DECISION_LOG.md](../DECISION_LOG.md). With dependencies installed and generated artifacts present, run:

```powershell
py -m evaluation.run_all --labels data\\golden\\spotifycares_intent_golden.csv
py -m scripts.run_spotify_agent --message "My Spotify app will not play songs on my iPhone"
```

The full raw dataset is not required for the second command once `data/processed/spotifycares_cases.jsonl` exists. Source: Kaggle TWCS, [thoughtvector/customer-support-on-twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter).
