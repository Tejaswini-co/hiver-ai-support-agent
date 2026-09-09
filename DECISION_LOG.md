# Decision Log

1. **Select the exact support handle `SpotifyCares`:** full-data analysis found no explicit brand column, so the canonical identity is the observed outbound `author_id`; SpotifyCares balances 15,096 linked customer messages with the strongest direct-reply coverage among the top candidates.
2. **Use a schema-tolerant census:** Kaggle exports can vary in column naming and packaging.
3. **Use TF-IDF first:** it is lightweight, reproducible, inspectable, and establishes a credible baseline before adding an embedding service.
4. **Keep retrieval exclusion explicit:** evaluation code can exclude held-out IDs and conversation IDs rather than silently leaking answers.
5. **Use case-level evidence objects:** customer and agent text remain linked for grounded drafting.
6. **Escalate low confidence:** a wrong confident support answer is costlier than a review request.
7. **Escalate security-sensitive terms:** account compromise needs human handling even when lexical similarity is high.
8. **Draft from historical agent text:** the first generator is evidence-constrained and cannot pretend an action occurred.
9. **Keep LLM use optional:** core reproduction should not require an API key.
10. **Do not create golden labels automatically:** the assignment requires real manual labels, not synthetic evaluation.
11. **Do not report headline metrics before execution:** numbers without generated artifacts would be misleading.
12. **Keep `other_unclear`:** terse acknowledgements and context-dependent Twitter replies cannot be reliably assigned to a support problem from one message.
13. **Use grouped rather than row-level splitting:** reply-linked messages from one conversation are not independent observations.
14. **Treat direct reply as evidence, not resolution truth:** a support reply does not prove the customer was satisfied or the issue was fixed.
15. **Separate provisional, reviewed, and independent evaluation artifacts:** this makes the circular-label limitation visible instead of hiding it in metrics.