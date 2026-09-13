# direct_grading_v1 (baseline B2 only — not the product path)

You are grading a whole submission against a whole rubric in one pass.

Return a JSON object `{"criteria": [...]}` with one item per rubric criterion:

```json
{"criterion_id": "C1", "sufficiency": "sufficient | partial | insufficient",
 "provisional_score": 3.0, "score_max": 4.0, "explanation": "..."}
```

Use the rubric's own scale. This baseline receives the full document and is used
only to measure how often a one-shot grader makes claims without evidence.
