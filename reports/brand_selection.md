# Brand Selection

## Dataset overview

The census and full-data analysis were run on `data/raw/twcs.csv`.

- Rows: **2,811,774**
- Customer/inbound messages: **1,537,843**
- Company/outbound messages: **1,273,931**
- Unique values in `author_id`: **702,777**
- Rows with a non-null `in_response_to_tweet_id`: **2,017,439**
- Source columns: `tweet_id`, `author_id`, `inbound`, `created_at`, `text`, `response_tweet_id`, `in_response_to_tweet_id`

The values were computed by `scripts/census.py` and `scripts/analyze_brands.py`. No subsample was used for these counts.

## How support-account identity was determined

There is no explicit human-readable `brand` or `company` column. Instead:

- `inbound` is a boolean. `True` rows are customer messages; `False` rows are support/company messages.
- Outbound rows contain human-readable support handles in `author_id`, such as `AmazonHelp`, `AppleSupport`, and `SpotifyCares`.
- Inbound rows generally contain numeric customer IDs in `author_id`.
- `in_response_to_tweet_id` links a message to its immediate parent.

Therefore the analysis treats an exact outbound `author_id` value as a **support-account identity**. The selected value is the literal dataset value `SpotifyCares`; the dataset itself does not provide an independent company-name mapping. It is reasonable to read the handle as a Spotify support account, but the reproducible configuration uses the exact handle and does not rely on an invented mapping.

For a candidate account:

- **Linked inbound customer messages** are inbound rows whose parent is one of that account's outbound tweet IDs.
- **Company replies to linked customers** are outbound rows whose parent is one of those linked inbound customer IDs.
- **Customer-to-company response rate** is company replies to linked customers divided by linked inbound customer messages. This is an observable direct-reply proxy, not a claim that every case was resolved.
- **Customer messages with direct company reply** counts distinct linked inbound messages receiving at least one direct company reply.
- **Support tweets with customer children** counts outbound tweets that have at least one inbound child.

## Top five candidate support accounts

Candidates are ranked by outbound support volume, then compared using linked customer volume, direct response coverage, customer-account diversity, and usable text breadth. The ranking is deliberately not treated as a simple largest-account ranking.

| Rank | Support account | Outbound responses | Linked inbound messages | Customer accounts | Company replies to linked customers | Direct-reply rate | Customer messages with direct reply | Support tweets with customer children | Inbound vocabulary size |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `AmazonHelp` | 169,840 | 100,503 | 40,671 | 70,956 | 70.60% | 66,347 | 85,270 | 3,000*
| 2 | `AppleSupport` | 106,860 | 36,658 | 23,668 | 23,388 | 63.80% | 23,386 | 31,563 | 3,000*
| 3 | `Uber_Support` | 56,270 | 22,160 | 12,780 | 11,659 | 52.61% | 11,418 | 18,019 | 2,821
| 4 | `SpotifyCares` | 43,265 | 15,096 | 8,723 | 11,938 | **79.08%** | 11,501 | 13,762 | 2,089
| 5 | `Delta` | 42,253 | 14,470 | 8,034 | 10,669 | 73.73% | 9,075 | 11,992 | 2,434

\* The vocabulary calculation has a 3,000-term cap, so 3,000 means the cap was reached, not that the true vocabulary ends there.

## Selected support account: `SpotifyCares`

`SpotifyCares` is selected as the single implementation target.

### Why this is the best practical choice

1. **Sufficient evaluation volume:** 15,096 linked customer messages and 8,723 customer accounts are comfortably above what is needed for a stratified 150–250 example golden set.
2. **Strong historical reply coverage:** 11,501 linked customer messages have a direct company reply, and the observable direct-reply rate is 79.08%, the highest among the five largest candidates.
3. **Good RAG material:** there are 43,265 outbound support messages and 13,762 support tweets with customer children. This supplies many customer-to-support examples while preserving local response context.
4. **Manageable domain:** actual samples cover app behavior, playback, devices, account access, Premium status, playlists, and feature questions. This is broad enough for meaningful intents but narrower than a general retailer or airline corpus.
5. **Better response-style consistency:** sampled replies include concrete troubleshooting, requests for account details through DM, plan clarification, product limitations, and suggestions. These are useful historical behaviors for evidence-grounded drafting.
6. **Better experimental balance than selecting only by size:** AmazonHelp offers much more data, but sampled messages include multiple languages and a wider order/delivery/support surface. SpotifyCares gives enough data while reducing taxonomy and preprocessing complexity.
7. **Baseline and failure-analysis fit:** the focused domain supports interpretable TF-IDF features and manually reviewable errors, while 15k linked messages still supports held-out comparisons.

This is a pragmatic selection for a reproducible assignment, not a claim that SpotifyCares is the largest or universally best account.

## Recommended intent taxonomy

These are proposed categories for manual review and annotation, derived from actual `SpotifyCares` inbound messages and response examples. They are not yet golden labels or evaluation results.

| Intent | Evidence in actual linked inbound messages | Exploratory keyword matches* |
|---|---|---:|
| `playback_audio_issue` | playback, songs, shuffle, repeat, audio, sound | 2,818 |
| `app_technical_issue` | app errors, bugs, crashes, updates, version, not working | 4,910 |
| `account_access` | account, login/sign-in, password, email, access | 882 |
| `subscription_plan_billing` | Premium, subscription, cancellation, refund, charge, payment | 601 |
| `playlist_library_downloads` | playlists, albums, library, downloads, offline use | 1,427 |
| `device_platform_compatibility` | iPhone/iOS, Android, Windows, Mac, web, browser, speakers | 2,092 |
| `feature_or_policy_information` | how-to questions, feature availability, limitations, and product suggestions | reviewed from actual samples; no synthetic count claimed |
| `other_unclear` | ambiguous, multi-intent, unsupported, or insufficient-context messages | reserved category |

\* Keyword matches are overlapping exploratory signals, not labels, and are included only to show that each proposed area has observable support in the selected corpus. A manually reviewed taxonomy pass must define precedence for multi-intent messages and may merge or split categories before the golden set is created.

## Actual message evidence

Representative linked inbound messages include:

- “doesn’t work and i even tried deleting the app” (`app_technical_issue`)
- “Premium ... on shuffle it turns off when the song is done and just plays in order” (`playback_audio_issue`)
- “i have the most recent update for spotify” (`app_technical_issue` / `device_platform_compatibility`)
- “there is no way to manage Albums ... in the App” (`playlist_library_downloads` / `feature_or_policy_information`)
- “I tried it on web browser and it worked!” (`device_platform_compatibility`)

Representative outbound replies include requests to restart a device, requests to continue through DM, plan clarification, app reinstall guidance, a Windows Phone maintenance explanation, and suggestions to try a specific playlist. These examples support the proposed retrieval and response-grounding use case, but they are not themselves a quality score.

## Data-quality issues and limitations

- The dataset has no explicit brand/company mapping; the selected identity is the exact support handle `SpotifyCares`.
- `author_id` mixes support handles and customer identifiers, so account identity must be conditioned on `inbound=False`.
- Public Twitter messages contain noise, URLs, mentions, emojis, multilingual text, typos, and terse follow-ups such as “yes” or “DM sent”.
- A direct reply link is not proof of resolution, satisfaction, or policy correctness.
- Some conversations are incomplete because only the captured tweet graph is available; deleted or missing tweets can break context.
- The exploratory keyword counts overlap and are not human labels.
- The current response-rate statistic measures observed direct replies, not successful case closure.
- Near-duplicate and cross-split leakage still need to be handled when building the held-out golden set and retrieval index.
- The dataset does not prove that `SpotifyCares` is the legal or official company name; the implementation should preserve the handle as the canonical identifier.

## Decision

Configure the project with the exact observed support-account identifier `SpotifyCares`. Do not replace it with an unverified human-readable company name.