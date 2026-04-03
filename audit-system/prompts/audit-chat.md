# Claude Chat Audit Prompt

Read `~/Chat-gpt/audit-system/STATE.json` to confirm phase is "audit".

Audit the GrapplingMap website at https://aarontmaher.github.io/Chat-gpt/ from a product/UX perspective.

## What to evaluate
- First-time user experience (is the value proposition clear?)
- Information architecture (can users find what they need?)
- Feature discoverability (do users know what's available?)
- Onboarding flow (does the tutorial work? is Start Here useful?)
- Training workflow (drill → track → review cycle)
- Graph experience (is the 3D map useful or confusing?)
- Trust and credibility signals
- Mobile vs desktop experience differences
- Guest vs member value gap

## Output format
Write findings to `~/Chat-gpt/audit-system/audit-inbox/claude-chat.json`:

```json
{
  "agent": "claude-chat",
  "cycle": <from STATE.json>,
  "timestamp": "<ISO>",
  "findings": [
    {
      "id": "CC-001",
      "title": "Short description",
      "detail": "Product/UX analysis",
      "severity": "critical|high|medium|low",
      "category": "ux|conversion|trust|content|onboarding",
      "page": "/path or feature",
      "evidence": "What you observed",
      "suggested_fix": "Product recommendation",
      "effort": "easy|medium|large",
      "confidence": "high|medium|low"
    }
  ]
}
```

## After writing findings
Update STATE.json: set `audit_complete.claude_chat` to `true`.

## Rules
- Focus on product impact, not code implementation
- Be specific about user journeys that fail
- Distinguish "nice to have" from "blocking conversion"
- Do not suggest code changes — suggest outcomes
