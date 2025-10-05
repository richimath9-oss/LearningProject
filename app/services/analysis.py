from __future__ import annotations

from typing import Dict, List


MOSCOW_CATEGORIES = ["Must", "Should", "Could", "Won't"]


def build_gap_analysis(brd_markdown: str) -> Dict[str, List[str]]:
    missing = []
    clarifying = []
    if "performance" not in brd_markdown.lower():
        missing.append("Performance benchmarks")
    if "integration" not in brd_markdown.lower():
        clarifying.append("Which systems require integration?")
    if "security" not in brd_markdown.lower():
        missing.append("Security requirements detail")
    return {
        "missing_information": missing,
        "clarifying_questions": clarifying,
    }


def prioritize_requirements(brd_markdown: str) -> List[Dict[str, str]]:
    priorities: List[Dict[str, str]] = []
    for idx, line in enumerate(brd_markdown.splitlines(), start=1):
        line_lower = line.lower()
        if line_lower.startswith("1.") or line_lower.startswith("-"):
            if "must" in line_lower:
                bucket = "Must"
            elif "should" in line_lower:
                bucket = "Should"
            elif "could" in line_lower:
                bucket = "Could"
            else:
                bucket = MOSCOW_CATEGORIES[idx % len(MOSCOW_CATEGORIES)]
            priorities.append({
                "requirement": line.strip("- "),
                "priority": bucket,
            })
    return priorities
