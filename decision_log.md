# Decision log

1. **Brand selection — AppleSupport.** It has enough usable response-linked cases for a compact but credible experiment while keeping one brand's operational behavior coherent.
2. **Case reconstruction — response-linked customer/support pairs.** Rather than treating every tweet independently, the pipeline links inbound messages to AppleSupport response IDs. This is robust to the CSV's multi-ID response fields and keeps the support answer attached to its triggering customer turn.
3. **Intent taxonomy — 10 issue-level classes.** The taxonomy is deliberately small enough to evaluate while covering the dominant AppleSupport themes in the corpus; `other_services` absorbs genuinely out-of-taxonomy cases instead of forcing a false label.
4. **Unknown/other class.** A forced decision is often worse than an explicit fallback, especially for routing.
5. **Historical support memory.** Retrieval stores customer-message → support-reply examples instead of generic web knowledge. The agent therefore learns the brand's observed resolution behavior.
6. **TF-IDF retrieval for the first implementation.** Distinctive product/error tokens are important in Twitter support, and TF-IDF is cheap enough to reproduce in under 15 minutes on the committed sample. A hybrid dense retriever is the next-week experiment.
7. **Held-out IDs.** Golden examples are excluded from the retrieval/training pool to reduce memorization leakage.
8. **Trivial baseline.** Majority-intent is intentionally weak; its value is proving that headline accuracy is not meaningful by itself.
9. **Classical baseline.** TF-IDF + Logistic Regression gives a non-LLM comparator with transparent behavior.
10. **Drafting/routing separation.** The response generator proposes a solution; a separate risk gate decides whether that proposal is safe enough for public automation.
11. **Conservative financial/account policy.** Billing, refunds, payment-specific requests, account access/security, and secrets are not auto-handled publicly.
12. **Negative sentiment is not an automatic escalation trigger.** Emotion is treated as context, not as a safety boundary; operational risk matters more than tone alone.
13. **Historical private-handoff signal.** When multiple retrieved analogues were historically moved to DM/private support, the risk gate adds caution.
14. **LLM judge validation.** A 50-example candidate review sheet and an agreement script are included. Because no API key was available, the checked-in results intentionally do not claim an external LLM judge run or an agreement statistic.
15. **No frontend.** The assignment tests the data/AI/evaluation system, not UI polish; engineering time is concentrated on evidence, benchmarks, and failure analysis.
