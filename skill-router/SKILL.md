---
name: skill-router
description: Identify and route a user's current task to the most relevant installed Codex skill. Use when the user asks which skill to use, asks to select/route/recommend a skill, forgets what skills are installed, is unsure whether a skill exists, or explicitly wants the agent to inspect installed skills before working.
---

# Skill Router

Use this skill to choose the best installed skill for the current user request, then continue the task with that skill's instructions.

## Workflow

1. Restate the task as a short search query.
2. Check the skills already listed in the current conversation context. If one clearly matches, choose it.
3. If the match is unclear, run `scripts/rank_skills.py "<task query>" --top 8` from this skill directory.
4. Compare candidates by task fit, not just score:
   - Prefer skills whose description names the user's artifact, platform, tool, or workflow.
   - Prefer narrower skills over broad umbrella skills when both match.
   - Use the minimum skill set needed. Multiple skills are appropriate only when the task naturally crosses domains.
   - Do not choose this skill as the final destination unless the user's task is only skill discovery.
5. Read the selected skill's `SKILL.md` completely before acting. If it references task-relevant files, read only those referenced files.
6. Announce the selected skill briefly, then perform the user's task. Do not stop at a recommendation when the user asked for an actionable outcome.

## Ambiguity Rules

Ask one concise clarification only when the top candidates imply meaningfully different actions or external side effects. Otherwise, make a conservative choice and proceed.

If no installed skill fits, say that no dedicated installed skill appears to match, then use the best general approach.

If the selected skill cannot be read or its required tools are unavailable, state the blocker briefly and continue with the closest fallback.

## Helper Script

Run:

```bash
python scripts/rank_skills.py "summarize this Google Doc and resolve comments" --top 8
```

Useful options:

```bash
python scripts/rank_skills.py "build an ESP32 app" --roots "C:\Users\Lenovo\.codex\skills;C:\Users\Lenovo\.agents\skills"
python scripts/rank_skills.py "fix failing GitHub Actions" --json
```

The script scans installed `SKILL.md` files, parses `name` and `description`, and ranks candidates using deterministic token matching. Treat the output as evidence, then apply judgment.
