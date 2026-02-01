# Summarize Prompt Injection Mitigations

Consolidate and summarize all identified prompt injection mitigations from multiple chunks.

## All Identified Mitigations
```json
{{all_mitigations}}
```

## Task
1. Merge duplicate or similar mitigations
2. Consolidate related mitigations into cohesive descriptions
3. Prioritize by effectiveness
4. Combine source references for merged mitigations

## Response Format
Return a JSON array of consolidated mitigations:
```json
[
  {
    "mitigationFactor": "Consolidated description of the mitigation",
    "source": ["all relevant source references"]
  }
]
```

If no mitigations were found, return an empty array: `[]`
