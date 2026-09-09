# Golden-set annotation provenance

The 200-example set is a stratified reference set sampled from AppleSupport response-linked cases. Initial intent candidates were generated with the documented rules and the candidate reviewed the committed labels using the annotation policy. `annotation_corrections.csv` tracks any post-review changes.

Sampling target: 20 examples per each of the 10 defined intents. Golden tweet IDs are excluded from the retrieval pool. The final integrity check found no customer-ID or normalized-text overlap with the committed quick-evaluation sample.

The intent/action/must-contain fields are the reference labels used by the evaluation harness.
