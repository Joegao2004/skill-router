# Skill Router

<p align="center">
  <img src="skill-router/assets/social-preview.svg" alt="Skill Router preview" width="100%">
</p>

<p align="center">
  <a href="skill-router/SKILL.md"><img alt="Codex Skill" src="https://img.shields.io/badge/Codex-Skill-1D4ED8"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-10B981"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.9%2B-334155">
</p>

Skill Router is a Codex skill that helps an agent choose the best installed skill for the user's current task. It is useful when the user does not remember which skills are installed, is unsure which one applies, or wants Codex to inspect local skills before doing the work.

## What It Does

- Scans installed `SKILL.md` files from common Codex skill roots.
- Parses each skill's `name` and `description` metadata.
- Ranks candidate skills with deterministic token matching.
- Deduplicates repeated plugin-cache copies.
- Gives the agent a compact routing workflow before it reads the selected skill.

## When To Use It

Use `$skill-router` when a prompt sounds like:

```text
Which skill should I use for this?
Find the best installed skill for fixing GitHub Actions.
Route this task to the right skill.
I forgot what skills I have installed.
```

## Install

Clone this repository, then copy the `skill-router` folder into your Codex skills directory.

### macOS or Linux

```bash
git clone https://github.com/YOUR-ORG/skill-router.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skill-router/skill-router "${CODEX_HOME:-$HOME/.codex}/skills/skill-router"
```

### Windows PowerShell

```powershell
git clone https://github.com/YOUR-ORG/skill-router.git
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse -Force .\skill-router\skill-router "$env:USERPROFILE\.codex\skills\skill-router"
```

Replace `YOUR-ORG/skill-router` with your published repository path.

## Usage

In Codex:

```text
Use $skill-router to identify the most relevant installed skill for this task: debug a failing GitHub Actions check.
```

Run the helper script directly:

```bash
python skill-router/scripts/rank_skills.py "build a frontend dashboard with React" --top 8
```

Emit JSON for automation:

```bash
python skill-router/scripts/rank_skills.py "summarize a Google Doc" --json
```

## Example Output

```text
1. gh-fix-ci  score=134.591
   path: .../github/skills/gh-fix-ci/SKILL.md
   why: name:fix, description:failing, description:github, description:action
   description: Use when a user asks to debug or fix failing GitHub PR checks...
```

The score is a starting point. The agent should still apply judgment, prefer narrower skills when appropriate, and read the selected `SKILL.md` before acting.

## Repository Layout

```text
.
├── README.md
├── LICENSE
└── skill-router/
    ├── SKILL.md
    ├── agents/
    │   └── openai.yaml
    ├── assets/
    │   ├── icon-small.svg
    │   ├── icon-large.svg
    │   └── social-preview.svg
    └── scripts/
        └── rank_skills.py
```

## Publish To GitHub

From this folder:

```bash
git init
git add .
git commit -m "Publish skill-router"
gh repo create skill-router --public --source . --remote origin --push
```

## Validate

If you have the Codex `skill-creator` validation script available:

```bash
python path/to/skill-creator/scripts/quick_validate.py skill-router
```

The skill is intentionally small: the long-form public documentation lives in this README, while the installed skill stays compact for Codex context efficiency.
