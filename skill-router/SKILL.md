---
name: skill-router
description: Discover, compare, and diagnose installed Codex skills and their routing metadata. Use when the user asks what skills are installed, which skill might fit a task, why a skill was not found or did not trigger, how to improve a skill description, or when an explicit skill-routing recommendation needs evidence. This skill is a finder and routing doctor, not an automatic platform-level dispatcher.
---

# Skill Finder

Use this skill to inspect installed skills, explain routing evidence, and diagnose why a task did or did not match a skill. Treat it as a discovery and metadata-debugging tool, not as an authority that can automatically choose the right skill without judgment.

## Operating Modes

- **Find**: identify likely installed skills for a task.
- **Explain**: show why candidates matched, including matched and missing query terms.
- **Diagnose**: explain why an expected skill did not appear or ranked poorly.
- **Improve**: suggest concrete `description` wording that would make a skill easier to discover.
- **Route**: recommend the best next skill only when the evidence is strong enough, then read that skill's `SKILL.md` before doing the user's task.

## Workflow

1. Restate the user's task as a compact search query. For non-English requests, include a small English intent gloss when helpful.
2. If the user explicitly names a skill, respect that signal first. Read that skill's `SKILL.md`, then use this skill only to explain fit or metadata gaps.
3. Run `scripts/rank_skills.py "<task query>" --top 8` when the match is unclear or when the user wants evidence.
4. Interpret the results:
   - High coverage and a specific description usually means a good candidate.
   - Low coverage means the installed metadata may not cover the user's wording or no dedicated skill exists.
   - Broad skills can rank for generic words such as "write", "build", or "report"; do not treat that alone as strong evidence.
   - Prefer a narrower skill over a broad umbrella skill when both match the artifact, tool, or workflow.
5. When diagnosing a miss, inspect the expected skill's frontmatter:
   - Check whether `description` is present, readable, and not hidden by unusual YAML.
   - Compare the user's words with the skill's trigger words.
   - Suggest 1-3 concrete phrases to add to the description.
6. Only after choosing a target skill, read the selected skill's `SKILL.md` completely and follow its instructions.

## Output Shape

For skill discovery, answer with:

```text
Best candidate: <skill-name>
Confidence: strong | medium | weak
Why: <short evidence>
Gaps: <missing terms or reason for caution>
Next step: <read/use skill, ask clarification, or proceed without a dedicated skill>
```

For metadata diagnosis, answer with:

```text
Expected skill: <skill-name>
Diagnosis: <why it did or did not match>
Metadata issue: <specific problem>
Suggested description addition: <exact phrase>
```

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

The script scans installed `SKILL.md` files, parses `name` and `description`, ranks candidates, deduplicates plugin-cache copies, reports query-token coverage, and prints a diagnosis note. Treat the output as evidence, then apply judgment.
