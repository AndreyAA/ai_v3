# Verify Prompt Injection Mitigations

Review the previously identified prompt injection mitigations and verify their effectiveness.

## Original Text
```
{{chunk}}
```

## Previously Identified Mitigations
```json
{{previous_result}}
```

## Task
1. Verify each identified mitigation is genuinely protective
2. Remove ineffective or incorrectly identified mitigations
3. Refine mitigation descriptions if needed
4. Add any missed mitigations

## Response Format
Return a JSON array of verified mitigations:
```json
[
  {
    "mitigationFactor": "Description of the verified mitigation",
    "source": ["line or code reference where mitigation was found"]
  }
]
```

If no valid mitigations remain, return an empty array: `[]`
