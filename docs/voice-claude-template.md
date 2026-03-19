# GrapplingMap — Voice Claude Chat Template
# Paste this at the start of a new Claude voice chat session.
# Then speak naturally — Claude will read CLAUDE.md and results.md automatically.

---

I am working on a BJJ grappling reference app called GrapplingMap.
Read these two files to understand the current state:
1. https://raw.githubusercontent.com/aarontmaher/Chat-gpt/main/CLAUDE.md
2. https://raw.githubusercontent.com/aarontmaher/Chat-gpt/main/results.md

After reading both files:
- Read the plain_summary field from the latest result in results.md
- Read any decisions_needed questions from the latest result
- Tell me in simple terms what happened and what I need to decide
- Use plain conversational language — no code terms, no prompt IDs
- Tell me the top 3 pending tasks from CLAUDE.md in plain English
- Wait for my voice instructions

When I say "generate a prompt": output a properly formatted Code/Cowork prompt
between ---ZAPIER-PROMPT-START--- and ---ZAPIER-PROMPT-END--- delimiters.
I will copy it and fire it via Siri to Zapier.

Never invent BJJ technique names. All content decisions come from me (Aaron).
