"""Finds the fenced code blocks marked ``runnable`` in a page's Markdown."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

OPENING = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
# "runnable" or ".runnable" as a word of the info string: ```python runnable or ``` {.python .runnable}
FLAG = re.compile(r"(?:^|(?<=[\s{]))\.?runnable(?=[\s}]|$)")
LANG = re.compile(r"""(?:^|(?<=[\s{]))lang=(?:"([^"]*)"|'([^']*)'|([^\s}]+))""")


@dataclass
class Block:
    """A fenced code block marked runnable."""

    language: str  # the block's own language ("python"), or ""
    lang: str | None  # what lang= asks for, if anything
    code: str


def language_of(info: str) -> str:
    """The language an info string names: "python" for "python title=x" and for "{.python .x}"."""
    words = info.strip().strip("{}").split()
    for word in words:
        name = word.lstrip(".")
        if word.startswith("{") or "=" in word or name == "runnable":
            continue
        return name
    return ""


def without_flags(info: str) -> str:
    """The info string with runnable and lang= taken out, for a block that stays plain code."""
    return re.sub(r"\s+", " ", LANG.sub("", FLAG.sub("", info))).replace("{ ", "{").replace(" }", "}").strip()


def _dedent(line: str, indent: str) -> str:
    """The line without the fence's indentation (or as much of it as the line has)."""
    width = len(indent)
    stripped = line.lstrip(" \t")
    return line[width:] if len(line) - len(stripped) >= width else stripped


def replace_runnable(markdown: str, convert: Callable[[Block], str | None]) -> str:
    """Calls ``convert`` for each fenced block marked runnable, and puts the line it returns in
    place of the block, at the block's indentation. When it returns None the block stays code,
    with runnable and lang= taken out of its info string. Blocks inside other code blocks (a
    page showing the syntax itself) are left alone."""
    lines = markdown.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        opening = OPENING.match(lines[i])
        info = opening.group("info") if opening else ""
        # A backtick fence's info string can't hold a backtick (CommonMark), so ``` `x` ``` is code.
        if not opening or (opening.group("fence")[0] == "`" and "`" in info):
            out.append(lines[i])
            i += 1
            continue
        indent, fence = opening.group("indent"), opening.group("fence")
        closing = re.compile(rf"^[ \t]*{re.escape(fence[0])}{{{len(fence)},}}[ \t]*$")
        end = next((j for j in range(i + 1, len(lines)) if closing.match(lines[j])), None)
        if end is None:  # an unclosed fence runs to the end of the page
            out.extend(lines[i:])
            break
        if not FLAG.search(info):
            out.extend(lines[i : end + 1])
            i = end + 1
            continue

        asked = LANG.search(info)
        block = Block(
            language=language_of(info),
            lang=(asked.group(1) or asked.group(2) or asked.group(3) or "") if asked else None,
            code="\n".join(_dedent(line, indent) for line in lines[i + 1 : end]),
        )
        replacement = convert(block)
        if replacement is None:
            out.append(f"{indent}{fence}{without_flags(info)}")
            out.extend(lines[i + 1 : end + 1])
        else:
            # Blank lines around it, so it is a paragraph of its own wherever the fence was.
            out.extend(["", f"{indent}{replacement}", ""])
        i = end + 1
    return "\n".join(out)
