# AppleSupport Support Agent — Concise Evaluation Report

## 1. Scope and data

This project tests a narrow support-automation decision for **AppleSupport**: classify a public customer message, retrieve observed AppleSupport behavior, prepare a safe draft, and decide `AUTO-HANDLE` or `ESCALATE`. The source is ThoughtVector’s [Customer Support on Twitter (TWCS)](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter). The raw source CSV is excluded; the repository contains a 990-case, response-linked AppleSupport sample for reproducibility.

The taxonomy has 10 operational intents: account access, billing/payment, purchase/refund, subscription, connectivity, messages/calls, apps/App Store, battery/charging, software update, and device hardware. The prototype intentionally does not build customer accounts, payment handling, private-message execution, or a frontend.

## 2. System and safety boundary

`customer message → intent → TF-IDF support memory → draft → risk gate → decision`

Support Memory retrieves AppleSupport customer-message/support-reply pairs. The deterministic path uses named generic templates; it does **not** claim that its template text is historically grounded. It uses retrieval only for risk signals: semantic evidence strength and whether similar historical replies requested private follow-up.

The optional LLM path passes the three retrieved pairs to an OpenAI-compatible model and labels a successful response `llm_grounded`. Its prompt forbids invented policy, timelines, or public secret requests. A provider failure is surfaced as `deterministic_fallback`. The separate risk gate escalates account/security, financial, sensitive-information, persistent-failure, weak-evidence, and private-follow-up cases regardless of draft source.

## 3. Reference set and protocol

The committed golden set has **200** candidate-reviewed examples, exactly 20 for each intent. The set has zero duplicate IDs, zero duplicate normalized texts, and no ID/text overlap with the committed 990-case retrieval/training sample. Initial stratification was rule-assisted; the candidate reviewed labels under the documented policy, with corrections represented separately in `annotation_corrections.csv`. This is self-review rather than independent third-party annotation.

Evaluation excludes golden customer IDs from both the simple-baseline training rows and the Support Memory. The trivial baseline always emits `account_access`. The simple baseline is TF-IDF + logistic regression trained on weak deterministic labels. It is useful as a transparent baseline, but its label source is related to the rule benchmark and therefore is not an independent validation control.

## 4. Verified deterministic results

The final `python3 run.py --evaluate` run produced:

| System | Intent accuracy | Intent macro-F1 |
|---|---:|---:|
| Trivial baseline | 0.100 | 0.018 |
| TF-IDF + logistic regression | 0.600 | 0.570 |
| Rule intent benchmark | 0.910 | 0.833 |
| Support-memory + risk-gate agent | 0.910 | 0.833 |

Routing metrics for the deterministic agent: accuracy **0.940**; AUTO-HANDLE precision **0.969**; AUTO-HANDLE recall **0.912**; unsafe-auto rate **0.031** (3 of 98 gold escalations were AUTO-HANDLEd). The always-escalate routing baseline has 0.490 accuracy and 1.000 escalation recall.

The repository contains a runnable 50-example LLM-judge harness and a completed 50-row candidate-review sheet. Final validation completed all 50 external judge calls. The first 18 use `openrouter/free`; the remaining 32 use `gemini-3.6-flash` after free-provider limits. Per-row model provenance is recorded in `results/llm_judge_scores.csv`.

The genuine 50-row judge-vs-candidate comparison reports exact agreement / Cohen's kappa: correctness 0.26 / -0.045, groundedness 0.26 / -0.008, issue coverage 0.08 / -0.062, safety 0.92 / -0.020, tone 0.54 / 0.000, and total 0.16 / 0.031. The high safety exact agreement is notable, but the low kappas and mixed providers mean this is not evidence of strong, single-model evaluator reliability. No LLM quality claim is inferred from deterministic templates.

## 5. Failure analysis and misleading headline

Five observed examples from the final deterministic outputs:

1. **Account/App Store overlap — `G004`.** A Touch Bar/App Store message includes an Apple ID password; the classifier predicted `apps_appstore` instead of the account-access label. Routing still escalated.
2. **Payment hidden by update language — `G024`.** “Payment declined” alongside app-update language was predicted `software_update` rather than billing. The financial gate still escalated.
3. **Unsupported paraphrase — `G062`.** “Unsubscribe to an auto renewing app” fell to `other_services`, producing an unnecessary escalation for a gold AUTO-HANDLE case.
4. **Long-running failure under-modeled — `G189`.** A recurring iOS 11 screen-lockup was labeled device hardware but predicted software update and AUTO-HANDLEd, one of the three unsafe autos.
5. **Conservative persistence rule — `G192`.** A screen-freeze message after iOS 11 was escalated although the reviewed action is AUTO-HANDLE, showing the policy’s false-escalation cost.

The 0.910 intent and 0.940 routing headlines are not deployment claims. Rule-assisted sampling and weak-label training can make a related rule classifier look better than it would on independently annotated traffic. Routing accuracy also obscures the asymmetric cost of a false AUTO-HANDLE; unsafe-auto rate and AUTO precision are more meaningful operating metrics. This is a single-message benchmark, so it does not establish safe multi-turn support behavior.

## 6. Next week and attribution

Next, I would add a temporal holdout and independent annotations, calibrate abstention, test adversarial multi-intent messages, and separate historical *action* (public answer, DM, or handoff) from reply text. I would compare a hybrid sparse+dense retriever against TF-IDF and run the complete external judge plus the 50-row agreement analysis with a recorded model/provider configuration.

Data attribution: ThoughtVector, [Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter). No raw TWCS data or API secrets are included in this repository.
