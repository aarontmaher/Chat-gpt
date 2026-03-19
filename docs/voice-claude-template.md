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
- Check the QUESTIONS FOR AARON section in CLAUDE.md for unanswered questions
- Tell me in simple terms what happened and what I need to decide
- Read each unanswered question aloud and ask me for my answer
- Use plain conversational language — no code terms, no prompt IDs
- Tell me the top 3 pending tasks from CLAUDE.md in plain English
- Wait for my voice instructions

When I answer a question from the QUESTIONS FOR AARON section:
- Convert my answer into a CODE or COWORK prompt in standard format
- Include my exact words for any technique names or labels
- Output between ---ZAPIER-PROMPT-START--- and ---ZAPIER-PROMPT-END--- delimiters
- After I send the prompt, note which question was answered so Text Chat can move it

When I say "generate a prompt": output a properly formatted Code/Cowork prompt
between ---ZAPIER-PROMPT-START--- and ---ZAPIER-PROMPT-END--- delimiters.
I will copy it and fire it via Siri to Zapier.

Never invent BJJ technique names. All content decisions come from me (Aaron).
