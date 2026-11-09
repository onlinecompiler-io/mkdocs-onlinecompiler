"""The MkDocs plugin: code blocks marked ``runnable`` become editors readers can run.

A Markdown preprocessor finds the runnable blocks after snippets are included and before any code
block extension sees them, and stashes the widget's markup in their place: a div whose <pre> holds
the code. So no other extension can change the code, and the code is in the page as text.
"""

from __future__ import annotations

import html

from markdown import Extension, Markdown
from markdown.preprocessors import Preprocessor
from mkdocs.config import base
from mkdocs.config import config_options as c
from mkdocs.exceptions import PluginError
from mkdocs.plugins import BasePlugin, get_plugin_logger

from .fences import Block, replace_runnable
from .languages import compiler_for

log = get_plugin_logger(__name__)

WIDGET_URL = "https://onlinecompiler.io/widget.js"
KEYS_URL = "https://api.onlinecompiler.io/compilers/widgets/"

# Sets each "site" runner's data-theme from the page's light or dark mode, now and when the reader
# switches: Material for MkDocs keeps it on <body data-md-color-scheme>, MkDocs' own theme on
# <html data-bs-theme>. It runs again on each page Material's instant navigation brings in.
THEME_SCRIPT = """<script>(function () {
  function mode() {
    var scheme = document.body.getAttribute("data-md-color-scheme");
    if (scheme) return scheme === "slate" ? "dark" : "light";
    return document.documentElement.getAttribute("data-bs-theme") === "dark" ? "dark" : "light";
  }
  function apply() {
    var theme = mode();
    document.querySelectorAll('[data-onlinecompiler-theme="site"]').forEach(function (el) {
      if (el.getAttribute("data-theme") !== theme) el.setAttribute("data-theme", theme);
    });
  }
  apply();
  if (window.onlinecompilerThemeWatch) return;
  window.onlinecompilerThemeWatch = new MutationObserver(apply);
  window.onlinecompilerThemeWatch.observe(document.body, { attributes: true, attributeFilter: ["data-md-color-scheme"] });
  window.onlinecompilerThemeWatch.observe(document.documentElement, { attributes: true, attributeFilter: ["data-bs-theme"] });
})();</script>"""


class OnlineCompilerConfig(base.Config):
    key = c.Type(str, default="")
    theme = c.Choice(("site", "light", "dark", "auto"), default="site")
    languages = c.Type(dict, default={})


class RunnableExtension(Extension):
    def __init__(self, plugin: OnlineCompilerPlugin):
        super().__init__()
        self.plugin = plugin

    def extendMarkdown(self, md: Markdown) -> None:
        # After snippets (32) and whitespace normalising (30), before fenced code blocks (25).
        md.preprocessors.register(RunnablePreprocessor(md, self.plugin), "onlinecompiler", 28)


class RunnablePreprocessor(Preprocessor):
    def __init__(self, md: Markdown, plugin: OnlineCompilerPlugin):
        super().__init__(md)
        self.plugin = plugin

    def run(self, lines: list[str]) -> list[str]:
        convert = lambda block: self.plugin.runner(block, self.md)  # noqa: E731
        return replace_runnable("\n".join(lines), convert).split("\n")


class OnlineCompilerPlugin(BasePlugin[OnlineCompilerConfig]):
    def on_config(self, config):
        self.languages: dict[str, str] = {}
        for name, compiler in self.config.languages.items():
            resolved = compiler_for(str(compiler))
            if not resolved:
                raise PluginError(f'onlinecompiler: "languages": OnlineCompiler.io has no compiler "{compiler}" (for "{name}").')
            self.languages[str(name).strip().lower()] = resolved
        self.key = self.config.key.strip()
        if not self.key:
            log.warning(
                f'No widget key, so runnable code blocks show as plain code. Create a free one at {KEYS_URL} '
                'and set it as the plugin\'s "key" option.'
            )
        self.page = None
        self.page_runners = 0
        config.markdown_extensions.append(RunnableExtension(self))
        return config

    def on_page_markdown(self, markdown, page, config, files):
        # MkDocs renders one page at a time: this page's Markdown is converted next.
        self.page = page
        self.page_runners = 0
        return markdown

    def on_page_content(self, content, page, config, files):
        if not self.page_runners:
            return content
        # In the content rather than the page's <head>, so only pages with runners load the widget, and
        # Material's instant navigation runs it when it brings in such a page.
        loader = f'<script src="{WIDGET_URL}" async></script>'
        return content + loader + (THEME_SCRIPT if self.config.theme == "site" else "")

    def runner(self, block: Block, md: Markdown) -> str | None:
        """The placeholder for a runnable block's runner, or None to leave it as code."""
        if not self.key:
            return None
        name = block.lang if block.lang is not None else block.language
        compiler = compiler_for(name, self.languages)
        if not compiler:
            reason = f"OnlineCompiler.io doesn't run \"{name}\"" if name else "the code block has no language"
            where = f"{self.page.file.src_uri}: " if self.page else ""
            log.warning(f"{where}a runnable code block shows as plain code: {reason}.")
            return None
        self.page_runners += 1
        return md.htmlStash.store(self._markup(compiler, block.code))

    def _markup(self, compiler: str, code: str) -> str:
        theme = (
            'data-onlinecompiler-theme="site"' if self.config.theme == "site" else f'data-theme="{self.config.theme}"'
        )
        # A browser drops one newline straight after <pre>, so code starting with a blank line keeps it.
        text = html.escape(code, quote=False)
        if text.startswith("\n"):
            text = "\n" + text
        return (
            f'<div class="runcode onlinecompiler-runner" data-key="{html.escape(self.key)}" '
            f'data-lang="{html.escape(compiler)}" {theme} style="margin: 1em 0"><pre>{text}</pre></div>'
        )
