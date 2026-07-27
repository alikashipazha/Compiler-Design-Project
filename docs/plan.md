# Project Plan — Code-Aware IDE Feature Set for Python

**Course:** Compiler Design, K. N. Toosi University of Technology
**Team:** Ali Kashi Pazha (referred to below as **A**), Mohammad (referred to below as **B**)
**Status:** Awaiting approval. No code has been written yet.

This document is the engineering plan for the project described in
[`project_requirements.md`](project_requirements.md). It records the decisions we
made, the module contracts we commit to, the phase-by-phase milestones, the split
of work between the two team members, and the risks we expect to fight.

---

## 1. Decisions and Rationale

| Decision | Choice | Rationale |
| :--- | :--- | :--- |
| Target language (analyzed) | A documented subset of **Python 3**, called **MiniPy** | Small, familiar grammar; forces us to implement flow-sensitive type inference (§5.3.2), which is the more interesting half of the type-system requirement. Also gives us the LEGB example the requirements explicitly test (§5.2). |
| Implementation language | **Python 3.11+**, core with **zero third-party dependencies** | Fastest iteration, trivial HTML/ANSI emission, `pytest` + `coverage` available for the bonus. |
| Lexer engine | **Built from scratch**: our own regex parser → NFA (Thompson) → DFA (subset construction) → minimized DFA (Hopcroft) → maximal-munch simulation | Directly demonstrates §4.1 rather than asserting it. Self-contained and highly testable. |
| Parser strategy | Hand-written **recursive descent (LL(1) with bounded lookahead)**, plus precedence-climbing for the binary-operator ladder | The approach §4.3 names as most common for hand-written parsers. Bounded extra lookahead is used in a few documented places (see §4.3 of this plan). |
| Phase 3 interface | **Interactive CLI REPL** + **self-contained static HTML reports** | Satisfies §6.6 with the least protocol plumbing. A Web UI / LSP server remains on the bonus list. |
| Line/column convention | **1-based lines, 1-based columns**, plus a 0-based byte offset carried internally | Matches every example in the requirements (`factorial` at `1:5`, `loc=3:12`). Fixed once, in `core/source.py`, to avoid the classic off-by-one epidemic. |

### 1.1. Two Hard Rules

**Rule 1 — No parasitic use of the host language's own front end.** Because we are
writing Python that analyzes Python, we could accidentally (or lazily) import
`ast`, `tokenize`, `symtable`, `dis`, `compile`, `eval`, or `exec` and skip the
entire assignment. We also must not use the stdlib `re` module anywhere in the
lexer path, since our whole claim is that we built the regex engine ourselves.
This is enforced by an automated test (`tests/test_no_forbidden_imports.py`) that
scans `src/` for those imports and fails the build. `re` remains permitted in
developer tooling and tests, and this exemption is listed in the test itself.

**Rule 2 — The analyzer never executes the code it analyzes.** Everything is
static. No `import` of the target file, no sandboxing questions, no surprises.

### 1.2. A Theoretical Point Worth Documenting

Python's token stream is **not** a regular language. `INDENT`/`DEDENT` tokens
require an unbounded indentation *stack*, and `NEWLINE` suppression inside
brackets requires a bracket-depth counter. So our lexer is honestly described as
a **DFA plus a small auxiliary stack** — a pushdown-flavoured scanner. This is
not a shortcut; it is why real Python implementations do the same thing, and it
is a genuinely good talking point for the defense. We document precisely where
the regular part ends and the stack begins.

---

## 2. The MiniPy Subset

The subset is **frozen in writing before the parser is written** (deliverable:
`docs/language_subset.md`). Scope creep in the grammar is the single most likely
way this project runs late.

### 2.1. In Scope

- **Lexical:** identifiers, keywords, integer literals (decimal, `0x`, `0o`, `0b`, `_` separators), float literals (with exponent), string literals (single/double quoted, triple-quoted, raw `r""`, byte `b""`, and **f-strings without nested expressions** in Phase 1, extended later if time allows), `#` comments, all operators and delimiters including `:=`, `->`, `**`, `//`, `@`, and the augmented assignments, explicit line joining with `\`, implicit line joining inside `()[]{}`, and `INDENT`/`DEDENT`/`NEWLINE`/`ENDMARKER`.
- **Statements:** `expression`, assignment (including chained and augmented, and annotated `x: int = 5`), `if`/`elif`/`else`, `while`/`else`, `for`/`else`, `break`, `continue`, `pass`, `return`, `raise`, `try`/`except`/`else`/`finally`, `with`/`as`, `def` (with defaults, `*args`, `**kwargs`, and PEP 484 annotations), `class` (with base classes), `global`, `nonlocal`, `assert`, `del`, `import`/`from ... import`, `lambda`, decorators.
- **Expressions:** the full precedence ladder, chained comparisons, `and`/`or`/`not`, conditional expressions, calls with keyword arguments, attribute access, subscripting and slicing, list/dict/set/tuple displays, comprehensions (list/dict/set/generator), unary operators, `is`/`is not`/`in`/`not in`.

### 2.2. Explicitly Out of Scope (documented as known limitations)

`async`/`await`, `yield`/generators as a semantic feature (parsed, not analyzed
for flow), `match` statements, nested expressions inside f-strings (Phase 1),
metaclasses and `__slots__`, multiple-inheritance MRO subtleties (we use a
conservative over-approximation), `*`-unpacking in every syntactic position,
star-imports as a source of symbols, and any form of dynamic attribute access
(`getattr`, `setattr`, `__dict__` manipulation).

Every exclusion appears in `docs/limitations.md` with a one-line justification.
The requirements reward honest documentation of limits; they punish silent
crashes.

---

## 3. Repository Layout

```
project/
  README.md                      # overview, install, usage, CI badge
  pyproject.toml                 # packaging + pytest/coverage config
  Dockerfile                     # bonus
  .github/workflows/ci.yml       # bonus
  docs/
    project_requirements.md      # given
    plan.md                      # this file
    language_subset.md           # frozen MiniPy definition
    grammar.ebnf                 # REQUIRED Phase 1 deliverable (machine-readable)
    grammar.md                   # annotated grammar + FIRST/FOLLOW discussion
    token_specification.md       # formal regex for every token class
    architecture.md              # module map, data flow, interface contracts
    algorithms.md                # Thompson, subset, Hopcroft, LL(1), lattices, Tarjan
    diagnostics.md              # every diagnostic code, message, severity
    usage.md                     # user-facing guide for the CLI and REPL
    limitations.md               # known limits, per phase
    division_of_work.md          # who owns what (required by §8)
    traceability.md              # requirement section -> module -> test
  src/minipy_ide/
    core/                        # language-agnostic
      source.py                  # SourceFile, Position, Span
      diagnostics.py             # Severity, Diagnostic, DiagnosticBag
      tokens.py                  # TokenKind, Token
      automata/
        regex_syntax.py          # our regex mini-language -> regex AST
        nfa.py                   # Thompson construction
        dfa.py                   # subset construction + priorities
        minimize.py              # Hopcroft
        scanner.py               # maximal-munch DFA simulation
      lexer.py                   # generic spec-driven lexer + trivia handling
      ast_base.py                # Node base: span, parent, walk, innermost_at
      parsing.py                 # TokenCursor, expect/consume, panic-mode sync
      symbols.py                 # Symbol, Scope, SymbolTable
      types.py                   # type lattice, join, assignability, members
      cfg.py                     # BasicBlock, CFG, edge kinds, rendering
      dataflow.py                # generic worklist fixed-point solver
      analyses.py                # definite assignment, liveness, reaching defs
      callgraph.py               # graph + BFS/DFS/Tarjan queries
      reference_index.py         # goto-def / find-refs / hover backing store
      rename.py                  # scope-aware rename + unified diff
      highlight.py               # Category enum + classifier
      render_ansi.py
      render_html.py
      completion.py
    languages/
      registry.py                # LanguageSpec plugin registry
      minipy/
        token_spec.py            # the formal token regexes
        layout.py                # INDENT/DEDENT/NEWLINE off-side rule
        nodes.py                 # MiniPy AST node types
        parser.py                # recursive-descent parser
        binder.py                # scope + symbol construction (LEGB)
        typer.py                 # flow-sensitive inference + annotation checking
        builtins.py              # builtin functions and stdlib member tables
        cfg_builder.py           # MiniPy statements -> CFG
        highlight_rules.py       # AST/symbol-aware category mapping
      # c/                       # bonus: second language plugin
    cli/
      main.py                    # subcommands
      repl.py                    # interactive Phase 3 shell
      report.py                  # HTML bundle generator
  tests/
    fixtures/
      valid/                     # syntactically and semantically clean
      lexical_errors/
      syntax_errors/
      semantic_errors/
      golden/                    # expected outputs, one file per fixture/command
    test_regex_engine.py  test_dfa_minimization.py
    test_lexer.py  test_layout.py  test_parser.py  test_recovery.py
    test_binder.py  test_typer.py  test_completion.py
    test_cfg.py  test_dataflow.py  test_callgraph.py
    test_navigation.py  test_rename.py  test_highlight.py
    test_robustness.py            # fuzz: must never raise, must always terminate
    test_no_forbidden_imports.py  # enforces Rule 1
  examples/                       # canonical demo programs
```

---

## 4. Module Contracts

These are the interfaces both members code against. They are fixed in **Phase 0**
so that all later work can proceed in parallel. Changing one of these after
Phase 0 requires agreement from both members, because it breaks the other
person's work.

### 4.1. Source and Diagnostics

```python
@dataclass(frozen=True)
class Position:
    line: int      # 1-based
    column: int    # 1-based
    offset: int    # 0-based index into the source text

@dataclass(frozen=True)
class Span:
    file: str
    start: Position
    end: Position          # exclusive
    @property
    def length(self) -> int: ...

@dataclass
class Diagnostic:
    severity: Severity     # ERROR | WARNING | INFO
    code: str              # stable id, e.g. "LEX001", "SEM010"
    message: str
    span: Span
    notes: list[str] = field(default_factory=list)
    def to_json(self) -> dict: ...   # severity, code, message, file, line, column, length
```

Two things to note. First, `length` is a first-class field because §5.5 requires
diagnostics to underline the exact offending span — this is why we carry spans
everywhere rather than bare positions. Second, every diagnostic gets a **stable
code**. Codes make golden-file tests robust against message rewording and give
`docs/diagnostics.md` something to be indexed by.

### 4.2. Tokens and Trivia

The lexer emits **every** token, including comments, whitespace-significant
layout tokens, and `INVALID`. The parser consumes a *filtered view* of that
stream. This matters because §4.5 requires the highlighted output to be a
faithful rendering of the original source: if the highlighter has the full
stream, faithful reproduction is trivial, whereas re-attaching discarded trivia
later is fiddly and bug-prone.

```python
@dataclass(frozen=True)
class Token:
    kind: TokenKind
    lexeme: str
    span: Span
    def is_trivia(self) -> bool: ...   # COMMENT, WHITESPACE, LINE_CONTINUATION
```

### 4.3. Parser Contract

Recursive descent, one function per non-terminal, mirroring `docs/grammar.ebnf`
one-to-one so that grammar and code can be diffed by eye during the defense.

Three places need documented lookahead beyond one token, and we will call them
out honestly in `docs/grammar.md` rather than pretending the grammar is pure
LL(1):

1. **Assignment vs expression statement.** We parse an expression, then, if we
   see `=`, validate that what we parsed is a legal assignment target and convert
   it in place. This is the standard approach and avoids a hostile left-factoring.
2. **Parenthesized expression vs tuple vs generator expression.**
3. **Lambda parameter lists**, which are comma-separated without brackets.

Error recovery is **panic mode** (§4.3.3), with MiniPy synchronization points:
`NEWLINE`, `DEDENT`, and the statement-introducing keywords (`def`, `class`,
`if`, `while`, `for`, `return`, `try`, `with`, `import`). The parser always
returns a tree — possibly containing `ErrorNode` placeholders — never `None`, and
never raises.

### 4.4. Symbols and Scopes

Fields are exactly the nine required by §5.1 (`name`, `kind`, `type`, `scope`,
`definition_loc`, `references`, `signature`, `is_initialized`, `is_used`), plus
MiniPy-specific flags for `global`/`nonlocal`/builtin.

Scope kinds: `BUILTIN` (root, preloaded) → `MODULE` → `FUNCTION` / `CLASS` /
`COMPREHENSION`. Three Python-specific resolution rules we implement and
document, because each one is a place a naive implementation gets it wrong:

- **Class scopes are not enclosing scopes for nested functions.** A method body
  does not see class-level names via the scope chain.
- **Comprehensions have their own scope** in Python 3.
- **Binding is by assignment, function-wide.** A name assigned anywhere in a
  function body is local to the *entire* body, including textually earlier lines.
  This is exactly why §5.1.2's two-pass strategy is mandatory rather than
  optional for us: pass 1 collects all bindings in a scope, pass 2 resolves uses.
  It also produces the `UnboundLocalError`-style "use before initialization"
  warning that §5.5 asks for.

### 4.5. Type Lattice

```
Unknown (top)
  |
  +-- None, Bool, Int, Float, Str, Bytes
  +-- List[T], Set[T], Dict[K,V], Tuple[T1..Tn]
  +-- Callable(params, ret)
  +-- Instance(ClassSymbol), Class(ClassSymbol), Module(name)
  +-- Union[...]
  |
Never (bottom)
```

`join(a, b)` is the least upper bound, used at control-flow merge points.
`is_assignable(src, dst)` drives assignment and argument checking. Because
MiniPy is dynamically typed we combine two sources of truth: **flow-sensitive
inference** for unannotated code, and **PEP 484 annotations** where the
programmer supplied them. This is precisely how Pyright — named in the
requirements' own footnote — behaves, and it lets us report the concrete
argument-type and return-type mismatches that §5.5 requires without inventing a
type system Python does not have.

`member_lookup(type, name)` backs `.`-completion and is fed by curated member
tables for `str`, `list`, `dict`, `set`, `int`, `float`, and `bytes` in
`builtins.py`. This is the Python analogue of the requirements' Java
`String s = "hello"; s.|` example.

### 4.6. CFG and the Data-Flow Framework

The solver is written **once**, generically, and instantiated three times. This
is the single biggest leverage point in Phase 3.

```python
class Analysis(Protocol):
    direction: Direction          # FORWARD | BACKWARD
    def boundary(self) -> State: ...
    def initial(self) -> State: ...
    def join(self, a: State, b: State) -> State: ...
    def transfer(self, block: BasicBlock, state: State) -> State: ...

def solve(cfg: CFG, analysis: Analysis) -> dict[BlockId, State]:
    """Worklist iteration to a fixed point."""
```

- **Definite assignment**: forward, must-analysis, join = intersection (§6.1.1).
- **Live variables**: backward, may-analysis, join = union (§6.1.1).
- **Reaching definitions**: forward, may-analysis, join = union — needed for dead-assignment detection (§6.5).

Edge kinds are labelled (`UNCONDITIONAL`, `TRUE`, `FALSE`, `LOOP_BACK`,
`EXCEPTION`, `RETURN`) so the CFG renders legibly and so exception edges can be
excluded from analyses where that is the right approximation. The `try/finally`
construct is the hard case; our approximation (every statement in the `try` may
jump to every handler; `finally` sits on all exit paths) is documented in
`docs/limitations.md`.

---

## 5. Phases and Milestones

Durations are relative and must be calibrated against the real submission dates
once we have them.

### Phase 0 — Foundations (short, both members together)

Everything in §4 above, as code with tests but no behavior: `source.py`,
`diagnostics.py`, `tokens.py`, `ast_base.py`, the `LanguageSpec` registry, the
CLI skeleton, the fixture/golden test harness, `pyproject.toml`, and the Rule 1
guard test.

*Exit criteria:* `pytest` runs green; `minipy-ide --help` works; both members have
signed off on the interfaces in §4.

### Phase 1 — Lexical Analysis and Syntax Highlighting

Deliverables:

1. `docs/token_specification.md` — the formal regular expression for **every**
   token class, plus an explanation of how they compose into one DFA and how
   longest-match and keyword-before-identifier priority are resolved (§4.1
   requires this explicitly).
2. The regex→NFA→DFA→minimized-DFA engine, with tests that check the minimized
   DFA accepts exactly the same language as the NFA on generated inputs, and that
   Hopcroft actually reduces state count on a known example.
3. The MiniPy lexer: DFA simulation with maximal munch, plus the layout pass
   (`INDENT`/`DEDENT`/`NEWLINE`, bracket-depth suppression, explicit line
   joining). Error recovery per §4.2.3: `INVALID` token, advance one character,
   continue; detect unterminated strings and, for MiniPy, unterminated
   triple-quoted strings.
4. `docs/grammar.ebnf` — the complete EBNF grammar (**required deliverable**).
5. `tools/grammar_check.py` — reads `grammar.ebnf`, computes FIRST/FOLLOW sets,
   and reports conflicts. This converts "our grammar is unambiguous" from a claim
   into a checked artifact, which is what §4.3 actually asks for.
6. The recursive-descent parser with panic-mode recovery, producing an AST where
   every node carries a span and a null type slot.
7. The highlighter: **AST- and symbol-aware**, not regex-based (§4.4 states
   plainly that a regex highlighter earns no credit). It must distinguish a
   called name from a variable, a class name from a function name, and a
   decorator from an operator `@`.
8. ANSI and self-contained-HTML renderers (§4.5), both round-tripping the source
   text exactly.

*Exit criteria:* every fixture in `valid/`, `lexical_errors/`, and
`syntax_errors/` produces correct golden output; the fuzz robustness test passes;
a deliberately broken file still highlights every valid region.

### Phase 2 — Semantic Analysis and Intellisense

1. Symbol table with the full scope tree, the two-pass strategy, and all nine
   required fields per symbol.
2. LEGB name resolution, including the three Python-specific rules in §4.4 above.
   Undefined-symbol errors and shadowing warnings (§5.2).
3. Flow-sensitive type inference plus annotation checking; `isinstance` narrowing
   if time permits (it is a small addition on top of the branch-sensitive
   environment we need anyway).
4. The complete diagnostic catalogue of §5.5, each with a stable code, and
   `docs/diagnostics.md` indexed by code.
5. The completion engine: context detection (after `.`, at statement start, inside
   an argument list, after `import`), symbol-table query for visible symbols,
   prefix-then-fuzzy ranking, and structured results with `label`, `kind`,
   `detail`, `sortOrder`.
6. Hover information: type signature, enclosing scope, and docstring extraction.

*Exit criteria:* every fixture in `semantic_errors/` yields exactly the expected
diagnostics; completion at a set of marked cursor positions returns the expected
ranked lists; the LEGB example from §5.2 of the requirements resolves correctly.

### Phase 3 — Program Analysis, Navigation, Refactoring

1. CFG construction for every function and for module top level, covering all
   MiniPy control constructs including `try/except/finally` and loop `else`.
2. The generic data-flow solver, then definite assignment, live variables, and
   reaching definitions on top of it.
3. Unreachable-block and post-jump statement detection (§6.1.1).
4. Call graph with direct-call resolution via the symbol table and conservative
   virtual-dispatch over-approximation via the class hierarchy; plus every query
   in §6.2.1, including Tarjan's SCC algorithm and recursion detection.
5. Go-to-definition, find-all-references, and hover, with JSON output matching
   the shape shown in §6.3.
6. Safe rename: conflict check, shadow check, unified diff, atomic application.
   Text substitution is explicitly worth zero credit, so this is driven entirely
   off resolved symbol references.
7. The five dead-code categories of §6.5.
8. The interactive CLI REPL (`goto-def`, `find-refs`, `rename`, `show-cfg`,
   `callgraph`, `dead-code`, ...) and the HTML report bundle.

*Exit criteria:* CFGs for a curated set of functions match hand-drawn expected
graphs; rename on two same-named variables in different scopes touches only one;
all §6.5 categories are detected in the requirements' own example program.

---

## 6. Division of Work

Team size is two, and §9 says **each member will be questioned on any component**.
So we deliberately avoid "A owns the front end, B owns the back end" — that
pattern guarantees one member cannot answer half the questions.

Two mechanisms enforce shared understanding:

- **Every change is reviewed by the other member** before it lands on `main`.
- **Each member writes the documentation for at least one module the *other*
  member implemented.** Writing the docs for someone else's code is the cheapest
  reliable way to be forced to actually read and understand it.

| Phase | Member A (Ali) | Member B (Mohammad) |
| :--- | :--- | :--- |
| 0 | `source`, `diagnostics`, `tokens`, CLI skeleton | `ast_base`, `LanguageSpec` registry, test harness, CI |
| 1 | Regex engine, NFA/DFA/Hopcroft, scanner, layout pass, token spec doc | `grammar.ebnf`, FIRST/FOLLOW tool, recursive-descent parser, AST nodes, panic recovery |
| 1 (joint) | Highlight classifier + ANSI renderer | HTML renderer + report scaffolding |
| 2 | Symbol table, scope tree, LEGB resolution, reference index | Type lattice, inference, annotation checking, diagnostic catalogue |
| 2 (joint) | Completion context detection | Completion ranking + hover |
| 3 | CFG builder, generic data-flow solver, the three analyses, dead code | Call graph + queries, goto-def/find-refs, safe rename + diff, REPL |
| Docs | `architecture.md`, `algorithms.md` (parsing + graphs — B's code) | `token_specification.md`, `diagnostics.md` (A's code), `usage.md` |

**Commit discipline** (required: 20+ meaningful commits distributed across both
members). Small, descriptive, imperative-mood commits scoped to one module, each
with its tests. Conventional-commit prefixes (`feat(lexer):`, `fix(parser):`,
`docs(grammar):`, `test(cfg):`) so the history reads as a narrative during the
defense.

---

## 7. Testing Strategy

Golden-file testing throughout: each fixture is a source file, and each expected
output is a checked-in snapshot for a given command. Adding a language feature
means adding a fixture and its snapshots.

The two tests that matter most are not feature tests:

- **`test_robustness.py`** — takes every fixture, generates mutations (truncation
  at random offsets, random character injection, bracket deletion, indentation
  scrambling) and asserts the full pipeline never raises and always terminates.
  §9 says crashing on bad input is grounds for significant deduction, so this
  test defends the highest-penalty requirement in the document.
- **`test_no_forbidden_imports.py`** — enforces Rule 1 from §1.1.

Target: ≥80% line coverage, which the bonus list asks for anyway.

---

## 8. Bonus Plan, in Priority Order

Ordered by value per unit of new machinery:

1. **Test suite + coverage report** — we want it regardless; the bonus is free.
2. **CI/CD via GitHub Actions** — run tests on push, generate the highlighted
   HTML for a canonical file, publish to GitHub Pages, badge in the README.
3. **Docker** — a `Dockerfile` so the whole thing runs with one `docker run`.
4. **Dominator tree → dominance frontier → SSA form** — the highest academic
   value on the list and pure reuse of the CFG we must build anyway. Lengauer-
   Tarjan for dominators, Cytron et al. for φ-placement.
5. **Second language plugin (a small C subset)** — proves the core really is
   language-agnostic, and adds *static* type checking to complement MiniPy's
   inference. This is the natural test of whether our plugin boundary is real.
6. **Automatic language detection** — a keyword-frequency and indentation-style
   classifier with confidence scores. Cheap and demos well, but only meaningful
   once there are two languages.
7. **Web UI or LSP server** — highest demo impact, highest risk. Only if Phase 3
   lands early.
8. **Incremental re-parsing** — most interesting, least likely to fit.

---

## 9. Risk Register

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| Python's layout rules (`INDENT`/`DEDENT`, implicit joining, continuations) are the buggiest part of the lexer | Blocks all of Phase 1 | Build the layout pass first, behind a dedicated `test_layout.py` with adversarial fixtures (blank lines in blocks, tabs mixed with spaces, comments at odd indentation, multi-line brackets) |
| f-strings with nested expressions are effectively a recursive sub-language | Medium | Phase 1 supports non-nested f-strings only; documented limit, revisited after Phase 2 |
| `try/finally` CFG edges have no single "correct" shape | Medium | Pick the standard conservative approximation, document it, and test the shape we chose |
| Python's dynamism (first-class functions, aliasing, `getattr`) breaks static call graphs | Medium | Resolve simple aliasing through inference; over-approximate virtual dispatch; document unresolved call sites as an explicit edge kind rather than dropping them silently |
| Grammar scope creep | High — the classic way this project runs late | `docs/language_subset.md` is frozen before the parser starts; additions require a written decision |
| Accidentally leaning on `ast`/`tokenize`/`re` | Fatal to the grade | Automated guard test (Rule 1) |
| Interfaces churning after Phase 0 and invalidating the other member's work | High | §4 contracts are agreed and reviewed at the Phase 0 gate; later changes need both members' sign-off |

---

## 10. Traceability

`docs/traceability.md` will map every numbered requirement section to the module
that satisfies it and the test that proves it. Building this incrementally, as
each feature lands, is far cheaper than reconstructing it the night before
delivery — and it is the document that makes the defense easy, because any
examiner question about "where is requirement X" has a one-line answer.

---

## 11. Immediate Next Steps

1. Approve or amend this plan.
2. Confirm the real submission deadlines so §5 can be calibrated.
3. Fill in the team details in `README.md` (student IDs, Mohammad's family name).
4. Initialize the Git repository and remote, then execute Phase 0.
