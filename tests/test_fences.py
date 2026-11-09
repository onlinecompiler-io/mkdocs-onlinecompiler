from mkdocs_onlinecompiler.fences import language_of, replace_runnable, without_flags
from mkdocs_onlinecompiler.languages import LANGUAGES, compiler_for

FENCE = "```"


def collect(markdown, answer="RUNNER"):
    blocks = []

    def convert(block):
        blocks.append(block)
        return answer

    return replace_runnable(markdown, convert), blocks


def test_every_compiler_is_listed():
    assert len(LANGUAGES) == 48


def test_names_resolve_to_compiler_ids():
    assert compiler_for("python") == "python-3.14"
    assert compiler_for("PY") == "python-3.14"
    assert compiler_for("c++") == "g++-15"
    assert compiler_for("sql") == "sqlite-3"
    assert compiler_for("python-3.14-pandas2") == "python-3.14-pandas2"
    assert compiler_for("brainfuck") is None
    assert compiler_for("__class__") is None
    assert compiler_for("") is None
    assert compiler_for("py", {"py": "python-3.14-pandas2"}) == "python-3.14-pandas2"


def test_a_runnable_block_is_replaced():
    out, blocks = collect(f"Intro\n\n{FENCE}python runnable\nprint(1)\n\nprint(2)\n{FENCE}\n\nAfter\n")
    assert out == "Intro\n\n\nRUNNER\n\n\nAfter\n"
    assert blocks[0].language == "python"
    assert blocks[0].lang is None
    assert blocks[0].code == "print(1)\n\nprint(2)"


def test_plain_blocks_are_left_alone():
    page = f"{FENCE}python\nprint(1)\n{FENCE}\n\n{FENCE}\nno language\n{FENCE}\n"
    out, blocks = collect(page)
    assert out == page
    assert blocks == []


def test_the_word_must_be_runnable():
    page = f'{FENCE}python title="runnable.py"\nx\n{FENCE}\n{FENCE}python notrunnable\nx\n{FENCE}\n'
    assert collect(page) == (page, [])


def test_info_string_forms():
    cases = {
        "python runnable": ("python", None),
        " python runnable": ("python", None),
        'python title="a.py" runnable lang=python-3.14-pandas2': ("python", "python-3.14-pandas2"),
        "py runnable lang='g++-15'": ("py", "g++-15"),
        'cpp runnable lang="g++-15-cpp20"': ("cpp", "g++-15-cpp20"),
        " {.python .runnable}": ("python", None),
        '{.cpp .runnable lang="g++-15"}': ("cpp", "g++-15"),
        "runnable": ("", None),
    }
    for info, expected in cases.items():
        _, blocks = collect(f"{FENCE}{info}\nx\n{FENCE}\n")
        assert (blocks[0].language, blocks[0].lang) == expected, info


def test_tilde_fences_and_longer_fences():
    out, blocks = collect("~~~js runnable\na\n```\nb\n~~~\n\n````go runnable\n```\nc\n````\n")
    assert [b.code for b in blocks] == ["a\n```\nb", "```\nc"]
    assert out.count("RUNNER") == 2


def test_a_block_inside_another_block_is_left_alone():
    page = f"````markdown\n{FENCE}python runnable\nprint(1)\n{FENCE}\n````\n"
    assert collect(page) == (page, [])


def test_indented_blocks_keep_their_indentation():
    page = f'!!! tip\n\n    {FENCE}rust runnable\n    fn main() {{\n        x();\n    }}\n    {FENCE}\n'
    out, blocks = collect(page)
    assert blocks[0].code == "fn main() {\n    x();\n}"
    assert "\n    RUNNER\n" in out


def test_an_unclosed_fence_is_left_alone():
    page = f"{FENCE}python runnable\nprint(1)\n"
    assert collect(page) == (page, [])


def test_a_backtick_fence_cannot_have_backticks_in_its_info():
    page = "``` runnable `x`\ncode\n```\n"
    out, blocks = collect(page)
    assert blocks == []


def test_a_block_that_stays_code_loses_the_flags():
    out, _ = collect(f'{FENCE}python title="a.py" runnable lang=python-3.14\nx\n{FENCE}\n', answer=None)
    assert out == f'{FENCE}python title="a.py"\nx\n{FENCE}\n'
    out, _ = collect(f"{FENCE} {{.python .runnable}}\nx\n{FENCE}\n", answer=None)
    assert out == f"{FENCE}{{.python}}\nx\n{FENCE}\n"


def test_helpers():
    assert language_of("{.python .runnable}") == "python"
    assert language_of('title="x" python') == "python"
    assert without_flags("python runnable") == "python"
