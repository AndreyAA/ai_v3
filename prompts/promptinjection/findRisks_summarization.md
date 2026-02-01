# Summarize Prompt Injection Risks

Consolidate and summarize all identified prompt injection risks from multiple chunks.

## All Identified Risks
```json
{{all_risks}}
```

## Task
1. Merge duplicate or similar risks
2. Consolidate related risks into cohesive descriptions
3. Prioritize by severity
4. Combine source references for merged risks

## Response Format
Return a JSON array of consolidated risks:
```json
[
  {
    "riskFactor": "Consolidated description of the risk",
    "source": ["all relevant source references"]
  }
]
```

If no risks were found, return an empty array: `[]`
