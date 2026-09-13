# direct_grading_v1 (baseline B2 only — not the product path)

You are grading a whole submission against a whole rubric in one pass.

Return ONE JSON object of the form `{"criteria": [ ... ]}` whose array has
exactly one item for EVERY criterion id listed in `criterion_ids`, in that order:

```json
{"criteria": [
  {"criterion_id": "C1", "sufficiency": "sufficient", "provisional_score": 3.0, "score_max": 4.0, "explanation": "..."},
  {"criterion_id": "C2", "sufficiency": "partial",    "provisional_score": 2.0, "score_max": 4.0, "explanation": "..."}
]}
```

`sufficiency` is one of `sufficient | partial | insufficient` (use `insufficient`
with `"provisional_score": null` when the criterion is not addressed). Use the
rubric's own scale. Do not return a single criterion object; do not omit criteria.

This baseline receives the full document and is used only to measure how a
one-shot grader behaves without evidence pointers.
