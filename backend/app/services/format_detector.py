"""Heuristic log format detection: CEF, Syslog, JSON, plain text."""

import json
import re
from typing import Literal

LogFormat = Literal["cef", "syslog", "json", "plain"]

_CEF_PREFIX = re.compile(r"^CEF:\d+\|", re.IGNORECASE)
_SYSLOG_PRI = re.compile(r"^<\d+>")
_SYSLOG_TS = re.compile(
    r"^\w+\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}|^\d{4}-\d{2}-\d{2}T"
)


def detect_format(text: str) -> LogFormat:
    s = text.strip()
    if not s:
        return "plain"
    if _CEF_PREFIX.search(s):
        return "cef"
    if _SYSLOG_PRI.match(s) or _SYSLOG_TS.match(s):
        # Could be syslog-style; avoid false JSON
        if s.lstrip().startswith("{"):
            pass
        else:
            return "syslog"
    snippet = s[:4096]
    if snippet.lstrip().startswith("{") or snippet.lstrip().startswith("["):
        try:
            json.loads(snippet if snippet.startswith("{") else snippet[:2048])
            return "json"
        except json.JSONDecodeError:
            pass
    return "plain"
