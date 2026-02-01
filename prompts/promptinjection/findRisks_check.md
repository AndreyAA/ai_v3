# Verify Prompt Injection Risks

Review the previously identified prompt injection risks and verify their validity.

## Original Text
```
{{chunk}}
```

## Previously Identified Risks
```json
{{previous_result}}
```

## Task
1. Verify each identified risk is a genuine prompt injection vulnerability
2. Remove false positives
3. Refine risk descriptions if needed
4. Add any missed risks

## Response Format
Return a JSON array of verified risks:
```json
[
  {
    "riskFactor": "Description of the verified risk",
    "source": ["line or code reference where risk was found"]
  }
]
```

If no valid risks remain, return an empty array: `[]`
