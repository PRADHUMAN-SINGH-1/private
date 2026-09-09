# Golden-set annotation policy

The gold set contains 200 examples, stratified 20 per intent across 10 operational intents discovered from AppleSupport customer language. Labels are issue-level: when a message mentions several concepts, choose the primary reason for contacting support.

## Intent labels
- `account_access`: Apple ID, iCloud, password, sign-in/account access.
- `billing_purchase`: charges, payment methods, receipts, purchase/payment problems that are not explicitly refund requests.
- `purchase_refund`: refunds, returns, unauthorized purchases, money-back requests.
- `subscription`: subscriptions, trials, renewals, cancellations.
- `connectivity`: Wi-Fi, Bluetooth, cellular/data, hotspot, network access.
- `messages_calls`: iMessage, SMS/text, FaceTime, calls, voicemail/notification delivery.
- `apps_appstore`: App Store/iTunes Store access, app install/download/crash/freeze problems.
- `battery_charging`: battery drain/health, charging, chargers, device heat while charging.
- `software_update`: iOS/macOS/software-update, restore, or update-related failures.
- `device_hardware`: screen/display, camera, keyboard, buttons, microphone/speaker, ports, physical hardware behavior.

## Routing labels
`AUTO-HANDLE` means a public, generic, non-sensitive procedural answer can reasonably be sent without account-specific verification. `ESCALATE` means the issue needs private/account-specific investigation, involves money/refunds, contains a high-risk failure signal, or lacks enough context for a safe public answer.

Negative sentiment alone is **not** an escalation trigger. Operational risk is the boundary.

## Sampling
Examples are selected from customer→AppleSupport response-linked cases, stratified by intent, deduplicated by tweet ID/text, and kept outside the committed retrieval sample.

The candidate should personally verify the 200 rows before submission; any changes belong in `annotation_corrections.csv`.
