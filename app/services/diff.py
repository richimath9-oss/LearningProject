from __future__ import annotations

import difflib


def render_diff(a: str, b: str) -> str:
    diff = difflib.unified_diff(
        a.splitlines(),
        b.splitlines(),
        lineterm="",
        fromfile="v1",
        tofile="v2",
    )
    return "\n".join(diff)
