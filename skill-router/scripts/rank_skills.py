#!/usr/bin/env python3
"""Rank installed Codex skills for a natural-language task query."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*", re.DOTALL)
STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "codex",
    "current",
    "do",
    "for",
    "from",
    "help",
    "how",
    "i",
    "in",
    "into",
    "is",
    "it",
    "me",
    "my",
    "new",
    "of",
    "on",
    "or",
    "please",
    "route",
    "select",
    "should",
    "task",
    "the",
    "this",
    "to",
    "use",
    "user",
    "using",
    "want",
    "what",
    "when",
    "which",
    "with",
}
ALIASES = {
    "builder": "build",
    "building": "build",
    "built": "build",
    "created": "create",
    "creates": "create",
    "creating": "create",
    "creator": "create",
    "extracted": "extract",
    "extracting": "extract",
    "extraction": "extract",
    "reviewed": "review",
    "reviewing": "review",
    "reviews": "review",
    "routed": "route",
    "router": "route",
    "routes": "route",
    "routing": "route",
}


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    path: Path
    score: float = 0.0
    reasons: tuple[str, ...] = ()
    coverage: float = 0.0
    matched_tokens: tuple[str, ...] = ()
    unmatched_tokens: tuple[str, ...] = ()


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}

    data: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip("\"'")
        data[key.strip()] = value
    return data


def normalize_token(token: str) -> str:
    token = token.lower()
    if token in ALIASES:
        return ALIASES[token]
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith(("ches", "shes")):
        return token[:-2]
    if len(token) > 4 and token.endswith(("xes", "zes")):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def tokenize(text: str, *, keep_stopwords: bool = False) -> list[str]:
    tokens = [normalize_token(token) for token in TOKEN_RE.findall(text)]
    if keep_stopwords:
        return tokens
    return [token for token in tokens if token not in STOPWORDS]


def default_roots() -> list[Path]:
    roots: list[Path] = []
    home = Path.home()
    codex_home = os.environ.get("CODEX_HOME")

    if codex_home:
        roots.append(Path(codex_home) / "skills")
    roots.extend(
        [
            home / ".codex" / "skills",
            home / ".codex" / "skills" / ".system",
            home / ".agents" / "skills",
            home / ".codex" / "plugins" / "cache",
        ]
    )

    seen: set[Path] = set()
    unique: list[Path] = []
    for root in roots:
        try:
            resolved = root.resolve()
        except OSError:
            continue
        if resolved not in seen and root.exists():
            seen.add(resolved)
            unique.append(root)
    return unique


def iter_skill_files(roots: Iterable[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("SKILL.md"):
            try:
                resolved = path.resolve()
            except OSError:
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            yield path


def load_skills(roots: Iterable[Path]) -> list[Skill]:
    skills: list[Skill] = []
    for path in iter_skill_files(roots):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue

        meta = parse_frontmatter(text)
        name = meta.get("name")
        description = meta.get("description")
        if not name or not description:
            continue
        skills.append(Skill(name=name, description=description, path=path))
    return dedupe_skills(skills)


def path_priority(path: Path) -> tuple[int, int]:
    raw = str(path).lower()
    if "\\.codex\\skills\\" in raw and "\\plugins\\cache\\" not in raw:
        return (0, len(raw))
    if "\\.agents\\skills\\" in raw:
        return (1, len(raw))
    if "openai-curated-remote" in raw:
        return (2, len(raw))
    if "openai-curated" in raw:
        return (3, len(raw))
    return (4, len(raw))


def dedupe_skills(skills: Iterable[Skill]) -> list[Skill]:
    by_key: dict[tuple[str, str], Skill] = {}
    for skill in skills:
        key = (skill.name.lower(), skill.description.strip().lower())
        current = by_key.get(key)
        if current is None or path_priority(skill.path) < path_priority(current.path):
            by_key[key] = skill
    return list(by_key.values())


def rank(skills: list[Skill], query: str) -> list[Skill]:
    query_tokens = list(dict.fromkeys(tokenize(query)))
    if not query_tokens:
        return skills

    docs = [
        tokenize(f"{skill.name} {skill.name.replace('-', ' ')} {skill.description}")
        for skill in skills
    ]
    doc_count = max(len(docs), 1)
    df: dict[str, int] = {}
    for tokens in docs:
        for token in set(tokens):
            df[token] = df.get(token, 0) + 1

    ranked: list[Skill] = []
    phrase = query.lower().strip()

    for skill, tokens in zip(skills, docs):
        token_counts: dict[str, int] = {}
        for token in tokens:
            token_counts[token] = token_counts.get(token, 0) + 1

        name_tokens = set(tokenize(f"{skill.name} {skill.name.replace('-', ' ')}"))
        desc_tokens = set(tokenize(skill.description))

        score = 0.0
        reasons: list[str] = []
        matched_tokens: list[str] = []
        for token in query_tokens:
            if token not in token_counts:
                continue
            matched_tokens.append(token)
            idf = math.log((doc_count + 1) / (df.get(token, 0) + 1)) + 1
            token_factor = 0.25 if token == "skill" else 1.0
            weight = 1.0
            if token in name_tokens:
                weight += 4.0
            if token in desc_tokens:
                weight += 2.0
            score += token_factor * weight * idf * (1 + math.log(token_counts[token]))
            if token in name_tokens:
                reasons.append(f"name:{token}")
            elif token in desc_tokens:
                reasons.append(f"description:{token}")
            else:
                reasons.append(f"matched:{token}")

        searchable = f"{skill.name} {skill.description}".lower()
        if phrase and phrase in searchable:
            score += 12.0
            reasons.append("exact-phrase")

        if score > 0:
            unmatched_tokens = [token for token in query_tokens if token not in matched_tokens]
            ranked.append(
                Skill(
                    name=skill.name,
                    description=skill.description,
                    path=skill.path,
                    score=round(score, 3),
                    reasons=tuple(dict.fromkeys(reasons)),
                    coverage=round(len(set(matched_tokens)) / len(query_tokens), 3),
                    matched_tokens=tuple(dict.fromkeys(matched_tokens)),
                    unmatched_tokens=tuple(unmatched_tokens),
                )
            )

    ranked.sort(key=lambda item: (-item.score, item.name, str(item.path)))
    return ranked


def parse_roots(raw_roots: str | None) -> list[Path]:
    if not raw_roots:
        return default_roots()
    return [Path(part).expanduser() for part in raw_roots.split(";") if part.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="+", help="Task request or search query")
    parser.add_argument("--top", type=int, default=10, help="Number of results to show")
    parser.add_argument(
        "--roots",
        help="Semicolon-separated skill roots. Defaults to common Codex skill roots.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    roots = parse_roots(args.roots)
    skills = load_skills(roots)
    results = rank(skills, " ".join(args.query))[: max(args.top, 1)]

    if args.json:
        print(
            json.dumps(
                [
                    {
                        "name": skill.name,
                        "score": skill.score,
                        "description": skill.description,
                        "path": str(skill.path),
                        "reasons": list(skill.reasons),
                        "coverage": skill.coverage,
                        "matched_tokens": list(skill.matched_tokens),
                        "unmatched_tokens": list(skill.unmatched_tokens),
                    }
                    for skill in results
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if not results:
        print("No matching installed skills found.")
        return 0

    if results[0].coverage < 0.5:
        print(
            "Warning: low query-token coverage. A dedicated installed skill may not exist; "
            "use judgment before routing."
        )
        print()

    for index, skill in enumerate(results, start=1):
        print(f"{index}. {skill.name}  score={skill.score}")
        print(f"   path: {skill.path}")
        print(f"   why: {', '.join(skill.reasons) if skill.reasons else 'matched query'}")
        print(
            f"   coverage: {len(skill.matched_tokens)}/"
            f"{len(skill.matched_tokens) + len(skill.unmatched_tokens)} tokens"
            + (
                f"; unmatched: {', '.join(skill.unmatched_tokens)}"
                if skill.unmatched_tokens
                else ""
            )
        )
        print(f"   description: {skill.description}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
