# Failure Analysis

These are five real response failures from `reports/human_review_outputs.jsonl`. They are based on actual customer messages, retrieved cases, generated responses, and the corresponding human-review artifact. They are qualitative observed failures, not statistically validated failure rates.

## 1. Generic account-change escalation for a solved interaction

- **Example:** `1852506`: “Janella P. From Spotify solved my problem! Please thank her...”
- **Expected:** Acknowledge that the issue was solved and pass on thanks.
- **Actual:** “We have not made any account changes here; a support specialist should review your request.”
- **Why it failed:** The classifier returned `other_unclear` with low confidence, and the fallback escalation draft ignored the positive resolution context.
- **Improvement:** Add a resolved/thanks dialogue state or classify acknowledgements separately before escalation.
- **Severity:** High, because it creates confusion and escalates a solved case.

## 2. Payment question answered with unrelated escalation

- **Example:** `773111`: “payment for student premium only via credit card or there will be another way?”
- **Expected:** Address payment-method availability using evidence, or explain that a human must verify account/payment details.
- **Actual:** Generic account-change escalation response.
- **Why it failed:** The model predicted `other_unclear`; retrieval contained payment-related historical cases, but the response generator did not use the best evidence when escalating.
- **Improvement:** Add intent-aware escalation drafts and require the response to mention the uncertainty relevant to payment methods.
- **Severity:** High, because billing questions need precise handling.

## 3. Audio problem not addressed

- **Example:** `89535`: “The app says that music is playing, but no sound comes out. I have to restart it...”
- **Expected:** Recognize an audio/playback issue and provide historically supported troubleshooting, such as reinstalling or testing another device.
- **Actual:** Generic account-change escalation response.
- **Why it failed:** The classifier predicted `other_unclear` with confidence below threshold despite highly relevant retrieved playback cases.
- **Improvement:** Use retrieval similarity and explicit playback signals in intent calibration; separate audio failures from generic unclear messages.
- **Severity:** High, because the customer receives no useful troubleshooting.

## 4. Account/profile migration question left unanswered

- **Example:** `1691143`: “Does that move an account, or just delete it along with the history and playlists?”
- **Expected:** Answer from historical evidence if supported, or explicitly say what information is missing before escalating.
- **Actual:** Generic escalation response that did not mention account history or playlists.
- **Why it failed:** Low classifier confidence triggered a fixed fallback draft, and the retrieved cases were mostly generic thank-you messages rather than account-migration examples.
- **Improvement:** Add account/profile-specific retrieval filters and evidence-quality thresholds before drafting.
- **Severity:** High, because the user asked a concrete account-data question.

## 5. Positive acknowledgement misclassified as a technical issue

- **Example:** `1362120`: “Can't believe you are so prompt... Your social listening abilities are super awesome.”
- **Expected:** Respond courteously to praise and avoid escalation.
- **Actual:** Predicted `app_technical_issue`, then produced a generic escalation response.
- **Why it failed:** The word `problem` appeared in praise/context text and triggered the keyword/TF-IDF classifier despite the message's overall positive intent.
- **Improvement:** Add a `resolved_or_feedback` intent or a sentiment/context guard before technical classification.
- **Severity:** Medium-high, because it damages tone and trust.

## Other measured diagnostic failures

- The classifier predicted `other_unclear` for all 40 held-out intent examples; macro-F1 was `0.09375`.
- The keyword baseline scored `1.0`, but its labels came from the same heuristic suggestion process, so the result is circular.
- Eleven of the 13 human-rated examples now have valid stored judge results; two still do not. The small agreement calculation is diagnostic only and does not validate failure rates.
