"""Lenient parsers for agent output. LLM output is never trusted to be
well-formed — every parser has a safe fallback so a run never dies on format.
"""

import re


def parse_scenes(text: str) -> list[dict]:
    """Expect lines 'SCENE: <title> | <seconds> | <description>'.
    Fallback: whole text becomes one scene."""
    scenes = []
    for match in re.finditer(r"^SCENE:\s*(.+)$", text, re.MULTILINE):
        parts = [p.strip() for p in match.group(1).split("|")]
        title = parts[0] if parts else "Scene"
        duration = 5.0
        description = ""
        if len(parts) >= 2:
            found = re.search(r"[\d.]+", parts[1])
            if found:
                try:
                    duration = min(float(found.group()), 600.0)
                except ValueError:
                    pass
        if len(parts) >= 3:
            description = " | ".join(parts[2:])
        scenes.append({"title": title[:200], "duration_s": duration, "description": description})
    if not scenes:
        scenes = [{"title": "Full piece", "duration_s": 60.0, "description": text.strip()[:2000]}]
    return scenes


def parse_seo(text: str) -> dict:
    """Expect 'TITLE:', 'DESCRIPTION:', 'TAGS:' markers; fallback to first line/body."""

    def grab(label: str) -> str:
        match = re.search(rf"^{label}:\s*(.+?)(?=^\w+:|\Z)", text, re.MULTILINE | re.DOTALL)
        return match.group(1).strip() if match else ""

    title = grab("TITLE")
    description = grab("DESCRIPTION")
    tags_raw = grab("TAGS")
    tags = [t.strip().lstrip("#") for t in re.split(r"[,\n]", tags_raw) if t.strip()][:30]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return {
        "title": (title or (lines[0] if lines else ""))[:200],
        "description": description or text.strip(),
        "tags": tags,
    }


def parse_opportunities(text: str) -> list[dict]:
    """Parse strategy director blocks separated by '---' with TOPIC/ANGLE/SCORES/WHY."""
    opportunities = []
    for block in re.split(r"^---\s*$", text, flags=re.MULTILINE):
        topic_match = re.search(r"^TOPIC:\s*(.+)$", block, re.MULTILINE)
        if not topic_match:
            continue
        angle_match = re.search(r"^ANGLE:\s*(.+)$", block, re.MULTILINE)
        why_match = re.search(r"^WHY:\s*(.+)$", block, re.MULTILINE)
        scores = {
            key: min(max(float(value), 0.0), 10.0)
            for key, value in re.findall(r"(\w+)=([\d.]+)", block)
        }
        opportunities.append(
            {
                "topic": topic_match.group(1).strip()[:500],
                "angle": angle_match.group(1).strip() if angle_match else "",
                "scores": scores,
                "rationale": why_match.group(1).strip() if why_match else "",
            }
        )
    return opportunities
