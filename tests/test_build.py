"""Builds small MkDocs sites with the plugin and checks the pages it writes."""

import html
import logging
import re
import textwrap

import pytest
from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.exceptions import Abort

FENCE = "```"
RUNNER = re.compile(r'<div class="runcode onlinecompiler-runner"([^>]*)><pre>(.*?)</pre></div>', re.S)

PAGE = f"""# Runnable

{FENCE}python runnable
print("hello")
{FENCE}

{FENCE}cpp runnable
#include <iostream>
int main() {{ std::cout << "a & b" << (1 < 2); }}
{FENCE}
Text straight after.

!!! tip

    {FENCE}py3 runnable lang=python-3.14-pandas2
    import pandas
    {FENCE}

{FENCE}python
print("plain")
{FENCE}

{FENCE}text runnable
not a language
{FENCE}

````markdown
{FENCE}python runnable
print("the syntax itself")
{FENCE}
````
"""


def make_site(tmp_path, plugin_config, theme="mkdocs", extra=""):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Home\n\nNo runnable blocks.\n")
    (tmp_path / "docs" / "runnable.md").write_text(PAGE)
    (tmp_path / "snippet.md").write_text(f"{FENCE}go runnable\npackage main\n{FENCE}\n")
    (tmp_path / "mkdocs.yml").write_text(
        f"site_name: Test\ntheme:\n  name: {theme}\nmarkdown_extensions:\n  - admonition\n{extra}"
        "plugins:\n  - onlinecompiler:\n" + textwrap.indent(plugin_config, "      ")
    )
    config = load_config(str(tmp_path / "mkdocs.yml"))
    build(config)
    site = tmp_path / "site"
    return (site / "runnable" / "index.html").read_text(), (site / "index.html").read_text()


def attr(attrs, name):
    match = re.search(rf'{name}="([^"]*)"', attrs)
    return match and match.group(1)


def test_runners_on_the_page(tmp_path, caplog):
    with caplog.at_level(logging.WARNING):
        page, home = make_site(tmp_path, "key: test-widget-key\nlanguages:\n  py3: python-3.14\n")
    runners = RUNNER.findall(page)
    assert [attr(a, "data-lang") for a, _ in runners] == ["python-3.14", "g++-15", "python-3.14-pandas2"]
    assert all(attr(a, "data-key") == "test-widget-key" for a, _ in runners)
    assert all(attr(a, "data-onlinecompiler-theme") == "site" for a, _ in runners)
    assert html.unescape(runners[1][1]) == '#include <iostream>\nint main() { std::cout << "a & b" << (1 < 2); }'
    assert "<iostream>" not in runners[1][1]
    assert html.unescape(runners[2][1]) == "import pandas"
    assert "Text straight after." in page
    assert "plain" in page and "not a language" in page and "the syntax itself" in page
    assert "wzxhzdk" not in page, "every placeholder is replaced"
    assert page.count('src="https://onlinecompiler.io/widget.js"') == 1
    assert "data-md-color-scheme" in page  # the theme script
    assert "widget.js" not in home, "pages without runners load nothing"
    assert 'doesn\'t run "text"' in caplog.text


def test_material_theme_with_superfences_and_snippets(tmp_path):
    pytest.importorskip("material")
    global PAGE
    page_before, PAGE = PAGE, PAGE + '\n--8<-- "snippet.md"\n'
    try:
        page, _ = make_site(
            tmp_path,
            "key: k\ntheme: dark\n",
            theme="material",
            extra=f"  - pymdownx.superfences\n  - pymdownx.snippets:\n      base_path: [{tmp_path}]\n      check_paths: true\n",
        )
    finally:
        PAGE = page_before
    runners = RUNNER.findall(page)
    # lang= names the third one's compiler, so the site's map isn't needed; the fourth is the snippet's.
    assert [attr(a, "data-lang") for a, _ in runners] == ["python-3.14", "g++-15", "python-3.14-pandas2", "go-1.26"]
    assert all(attr(a, "data-theme") == "dark" for a, _ in runners)
    assert "data-md-color-scheme" not in page.split("</article>")[0].split("<article")[-1]


def test_no_key_leaves_plain_code(tmp_path, caplog):
    with caplog.at_level(logging.WARNING):
        page, _ = make_site(tmp_path, "{}\n")
    assert RUNNER.findall(page) == []
    assert "widget.js" not in page
    assert "No widget key" in caplog.text
    # Without runnable and lang= in their info strings, they are ordinary code blocks again.
    for language in ("python", "cpp", "text"):
        assert f'class="language-{language}"' in page, language


def test_a_bad_language_map_fails_the_build(tmp_path, caplog):
    with pytest.raises(Abort):
        make_site(tmp_path, "key: k\nlanguages:\n  x: nope\n")
    assert 'no compiler "nope"' in caplog.text
