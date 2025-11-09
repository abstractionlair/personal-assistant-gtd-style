import json
import re
from typing import Any, Dict, Iterable, Optional, Set

_FENCE_PATTERN = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)


def _strip_first_fence(text: str) -> Optional[str]:
    """Return the contents of the first fenced block if present."""
    match = _FENCE_PATTERN.search(text)
    if not match:
        return None
    inner = match.group(1).strip()
    return inner or None


def _candidate_chunks(text: str) -> Iterable[str]:
    """Yield JSON candidate substrings ordered by likelihood."""
    trimmed = text.strip()
    if trimmed:
        yield trimmed

    fenced = _strip_first_fence(text)
    if fenced and fenced != trimmed:
        yield fenced

    if trimmed:
        brace_index = trimmed.find("{")
        if brace_index > 0:
            yield trimmed[brace_index:]


def parse_judge_verdict(text: str) -> Optional[Dict[str, Any]]:
    """Parse judge verdict text into a dictionary, tolerating Markdown fences."""
    decoder = json.JSONDecoder()
    seen: Set[str] = set()

    for chunk in _candidate_chunks(text):
        chunk = chunk.strip()
        if not chunk or chunk in seen:
            continue
        seen.add(chunk)

        try:
            data = json.loads(chunk)
        except json.JSONDecodeError:
            try:
                data, _ = decoder.raw_decode(chunk)
            except json.JSONDecodeError:
                continue

        if isinstance(data, dict):
            return data

    return None
