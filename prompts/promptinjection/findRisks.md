# Find Prompt Injection Risks

Analyze the following code/text chunk for potential prompt injection vulnerabilities.

Look for:
- User input that is directly concatenated into prompts
- Lack of input sanitization before LLM calls
- Dynamic prompt construction from untrusted sources
- Missing input validation or filtering
- Potential for instruction override attacks

## Input Text
```
{{chunk}}
```

## Response Format
Return a JSON array of identified risks:
```json
[
  {
    "riskFactor": "Description of the specific risk",
    "source": ["line or code reference where risk was found"]
  }
]
```

If no risks are found, return an empty array: `[]`
