# AppleSupport Support Agent — Evaluation Report

## 1. Problem framing

This project treats support automation as a **trust decision**, not simply a response-generation task. Good means the system identifies the customer's primary operational issue, finds evidence from the brand's historical support behavior, drafts a useful public response without inventing policy, and declines automation when risk or evidence quality is unfavorable.

The selected brand is **AppleSupport**. Brand screening on TWCS showed 106,860 AppleSupport outbound tweets and 106,622 usable response-linked customer/support cases after filtering. AppleSupport was chosen because it offers enough data while keeping the experiment focused on a coherent set of support problems.

**Not built:** a customer-account system, payment processing, private-message handling, a frontend, or web search. Those add surface area but do not improve the proof required by the assignment.

## 2. System

`Customer → intent → Support Memory → evidence/risk signals → draft → Risk Gate`

Support Memory stores customer-message/support-reply pairs. Retrieval is TF-IDF cosine similarity in the reproducible baseline. The LLM path supplies the top historical cases to the generator and explicitly forbids unsupported policy, invented timelines, and requests for secrets in a public tweet.

The Risk Gate is deliberately separate from drafting. It considers account/security signals, financial signals, intent confidence, retrieval strength, repeated failure, and evidence that similar historical cases were handled privately. Negative sentiment alone is **not** an escalation rule.

## 3. Golden evaluation set

The committed set contains 200 stratified examples, 20 per intent across 10 intents: account access, billing/payment, purchase/refund, subscription, connectivity, messages/calls, apps/App Store, battery/charging, software update, and device hardware. Golden IDs are excluded from the retrieval pool.

The candidate reviewed the 200 examples using the documented annotation policy; this is candidate-level annotation, not independent third-party labeling. Corrections are tracked in `data/golden/annotation_corrections.csv`.

## 4. Provisional results

The following results are from the deterministic pipeline on the 990-case committed sample and the current 200-row candidate reference set:

| System | Intent Accuracy | Intent Macro-F1 |
|---|---:|---:|
| Majority-intent trivial baseline | 0.100 | 0.018 |
| TF-IDF + Logistic Regression | 0.600 | 0.570 |
| Rule intent benchmark | 0.910 | 0.833 |
| Agent intent | 0.910 | 0.833 |

Routing:

| Metric | Result |
|---|---:|
| Accuracy | 0.940 |
| AUTO precision | 0.969 |
| AUTO recall | 0.912 |
| Unsafe-auto rate | 0.031 |

These results are based on the candidate-reviewed 200-example reference set and are the current headline metrics for the deterministic evaluation path.

The optional LLM generation path is implemented but was not executed in this environment because no API credential was provided. The repository deliberately does not manufacture LLM results.

## 5. Baselines

**Trivial baseline:** always predict one intent. With a balanced gold set, it reaches 10% accuracy and demonstrates why raw accuracy is a weak headline.

**Simple baseline:** TF-IDF + Logistic Regression trained on silver-labelled historical examples. It is transparent, fast, and does not use generation or historical response style.

The final live comparison should add the LLM path and answer a narrower question: does historical support evidence improve groundedness and routing safety over an LLM without Support Memory?

## 6. Top failure modes

**1. Primary-intent ambiguity.** A tweet may mention an update, battery, Wi-Fi, and crashing simultaneously. A single-label benchmark forces one primary issue. The system needs an explicit primary-issue policy.

**2. Account terms inside another task.** “Apple ID” can appear while the customer's actual problem is App Store or billing. Generic account keywords therefore create false account classifications.

**3. Charging vs billing language.** “Charge” has two meanings. The classifier must use local context rather than the token alone.

**4. Historical handoff does not equal semantic relevance.** A retrieved case can look similar but indicate that Apple historically moved that case into DM. Retrieval relevance should therefore increase caution rather than authorize automation.

**5. Multi-turn state is missing.** TWCS contains ongoing conversations. A single incoming message does not always contain enough state to decide safely, even if a similar historical case exists.

## 7. What is misleading about my headline number?

A routing accuracy such as **94.0%** sounds strong, but it hides asymmetric error costs. A false AUTO-HANDLE can be much worse than an unnecessary escalation. For that reason, the primary safety metric is **unsafe-auto rate** and the secondary operating metric is AUTO precision.

LLM-judge reply scores are also not truth. A judge can share linguistic preferences with the generator. I therefore included a 50-example candidate-reviewed reply-quality subset and a runnable judge-comparison harness. Because no external LLM API credential was available during development, **no judge-vs-human agreement statistic is claimed**; the checked-in agreement file explicitly records `NOT_RUN`.

Finally, the benchmark is primarily single-message evaluation. Strong results here do not prove safe long-running customer conversations.

## 8. One more week

I would add a hybrid BM25+dense retriever, calibrated abstention for intent classification, adversarial golden examples, and a temporal holdout. I would also model **historical support action** separately from reply generation so the system learns not only “what did support say?” but “did support answer publicly, ask for DM, or hand off?”
