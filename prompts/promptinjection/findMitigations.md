# Find Prompt Injection Mitigations

Analyze the following code/text chunk for existing prompt injection mitigations and protections.

Look for:
- Input sanitization and validation
- Prompt templating with proper escaping
- Input/output filtering mechanisms
- Role separation and system prompt protection
- Rate limiting or abuse prevention
- Content moderation or safety filters

## Input Text
```
{{chunk}}
```

## Response Format
Return a JSON array of identified mitigations:
```json
[
  {
    "mitigationFactor": "Description of the mitigation measure",
    "source": ["line or code reference where mitigation was found"]
  }
]
```

If no mitigations are found, return an empty array: `[]`
