"""The languages OnlineCompiler.io runs, and the names code blocks use for them."""

from __future__ import annotations

# Compiler id: (label, short name). Copied from https://onlinecompiler.io/docs/compilers at each
# release. A code block's language can be a compiler id or a short name; the first id with a short
# name is the one it picks.
LANGUAGES: dict[str, tuple[str, str]] = {
    "python-3.14":         ("Python 3.14", "python"),
    "gcc-15":              ("C (GCC 15)", "c"),
    "g++-15":              ("C++ (G++ 15)", "cpp"),
    "openjdk-25":          ("Java (OpenJDK 25)", "java"),
    "dotnet-csharp-10":    ("C# (.NET SDK 10)", "csharp"),
    "dotnet-fsharp-10":    ("F# (.NET SDK 10)", "fsharp"),
    "go-1.26":             ("Go 1.26", "go"),
    "rust-1.93":           ("Rust 1.93", "rust"),
    "php-8.5":             ("PHP 8.5", "php"),
    "ruby-4.0":            ("Ruby 4.0", "ruby"),
    "haskell-9.12":        ("Haskell (GHC 9.12)", "haskell"),
    "typescript-deno":     ("TypeScript (Deno)", "typescript"),
    "nodejs-24":           ("JavaScript (Node.js 24)", "javascript"),
    "sqlite-3":            ("SQL (SQLite 3)", "sql"),
    "duckdb-1.5":          ("DuckDB 1.5", "duckdb"),
    "bash-5.2":            ("Bash 5.2", "bash"),
    "gfortran-15":         ("Fortran (gfortran 15)", "fortran"),
    "dotnet-vbnet-10":     ("Visual Basic (.NET SDK 10)", "vbnet"),
    "kotlin-2.4":          ("Kotlin 2.4", "kotlin"),
    "r-4.6":               ("R 4.6", "r"),
    "swift-6.4":           ("Swift 6.4", "swift"),
    "gnucobol-3.2":        ("COBOL (GnuCOBOL 3.2)", "cobol"),
    "perl-5.44":           ("Perl 5.44", "perl"),
    "julia-1.13":          ("Julia 1.13", "julia"),
    "fpc-3.2":             ("Pascal (Free Pascal 3.2)", "pascal"),
    "octave-11":           ("Octave 11", "octave"),
    "nasm-3":              ("Assembly (NASM 3)", "assembly"),
    "lua-5.5":             ("Lua 5.5", "lua"),
    "ocaml-5.4":           ("OCaml 5.4", "ocaml"),
    "sbcl-2.6":            ("Common Lisp (SBCL 2.6)", "common-lisp"),
    "erlang-29":           ("Erlang (OTP 29)", "erlang"),
    "elixir-1.20":         ("Elixir 1.20", "elixir"),
    "swipl-10":            ("Prolog (SWI-Prolog 10)", "prolog"),
    "ldc-1.43":            ("D (LDC 1.43)", "d"),
    "fbc-1.10":            ("FreeBASIC 1.10", "freebasic"),
    "dart-3.13":           ("Dart 3.13", "dart"),
    "clojure-1.12":        ("Clojure 1.12", "clojure"),
    "groovy-6.0":          ("Groovy 6.0", "groovy"),
    "scala-3.10":          ("Scala 3.10", "scala"),
    "zig-0.17":            ("Zig 0.17", "zig"),
    "nim-2.2":             ("Nim 2.2", "nim"),
    "crystal-1.22":        ("Crystal 1.22", "crystal"),
    "gnat-15":             ("Ada (GNAT 15)", "ada"),
    "powershell-7.6":      ("PowerShell 7.6", "powershell"),
    "racket-9.3":          ("Racket 9.3", "racket"),
    "clang-objc-21":       ("Objective-C (Clang 21)", "objective-c"),
    "g++-15-cpp20":        ("C++20 (G++ 15)", "cpp"),
    "python-3.14-pandas2": ("Python 3.14 with pandas 2", "python"),
}

# Other names code blocks use for these languages (Pygments' and highlight.js's among them).
ALIASES: dict[str, str] = {
    "py": "python-3.14",
    "python3": "python-3.14",
    "c++": "g++-15",
    "c++20": "g++-15-cpp20",
    "cpp20": "g++-15-cpp20",
    "js": "nodejs-24",
    "node": "nodejs-24",
    "ts": "typescript-deno",
    "c#": "dotnet-csharp-10",
    "cs": "dotnet-csharp-10",
    "f#": "dotnet-fsharp-10",
    "golang": "go-1.26",
    "rs": "rust-1.93",
    "rb": "ruby-4.0",
    "hs": "haskell-9.12",
    "kt": "kotlin-2.4",
    "jl": "julia-1.13",
    "sqlite": "sqlite-3",
    "sh": "bash-5.2",
    "shell": "bash-5.2",
    "f90": "gfortran-15",
    "vb": "dotnet-vbnet-10",
    "asm": "nasm-3",
    "nasm": "nasm-3",
    "matlab": "octave-11",
    "lisp": "sbcl-2.6",
    "erl": "erlang-29",
    "ex": "elixir-1.20",
    "exs": "elixir-1.20",
    "clj": "clojure-1.12",
    "cr": "crystal-1.22",
    "ps1": "powershell-7.6",
    "pwsh": "powershell-7.6",
    "rkt": "racket-9.3",
    "objc": "clang-objc-21",
    "objectivec": "clang-objc-21",
}


def compiler_for(name: str | None, extra: dict[str, str] | None = None) -> str | None:
    """The compiler id for a language name ("python", "cpp", "python-3.14"), or None if
    OnlineCompiler.io doesn't run it. ``extra`` is the site's own map, checked first."""
    key = (name or "").strip().lower()
    if not key:
        return None
    if extra and key in extra:
        return compiler_for(extra[key])
    if key in LANGUAGES:
        return key
    if key in ALIASES:
        return ALIASES[key]
    for compiler_id, (_, short) in LANGUAGES.items():
        if short == key:
            return compiler_id
    return None
