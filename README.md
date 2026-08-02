# Compiler Design Project

This repository contains the implementation of the compiler design project for the Compiler Design course at the **Faculty of Computer Engineering**, **K. N. Toosi University of Technology**.

* **Semester:** Spring Semester 1404–1405
* **Instructor:** Dr. Alaeiyan

> ## Project Developer
> * **Ali Kashi Pazha** (Student ID: `40224641`)

---

# CC-IDE Code-Aware Analyzer & Compiler Front-End

[![CC-IDE Front-End CI/CD Pipeline](https://github.com/alikashipazha/Compiler-Design-Project/actions/workflows/ci.yml/badge.svg)](https://github.com/alikashipazha/Compiler-Design-Project/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)

A highly modular, professional-grade **Compiler Front-End** and **Static Program Analyzer** designed for a subset of the C programming language, implemented natively in Python. The system supports full lexical, syntactic, and hierarchical semantic analysis, and features advanced middle-end program analysis passes including Control Flow Graphs (CFG), Call Graphs, Dominator Trees, Static Single Assignment (SSA) form, safe rename refactoring, and an interactive CLI REPL.

---

## 🛠️ Key Architectural Features

### 1. Compiler Front-End Pipeline
*   **Hand-written DFA Lexer (`lexer.py`)**: Converts C source streams into typed token sequences. Handles multi-line comments, hexadecimal/binary integer literals, floats with scientific notation, escape sequences, and captures absolute position spans.
*   **Recursive-Descent Parser (`parser.py`)**: An LL(k) parser translated from an EBNF grammar. Builds a clean Abstract Syntax Tree (AST) while employing robust panic-mode synchronization to recover from syntax errors.
*   **AST-Guided Syntax Highlighter (`highlighter.py`)**: A context-aware renderer using the Visitor pattern to generate both ANSI colored terminal outputs and standalone tinned HTML/CSS webpages.

### 2. Semantic Analysis & Name Resolution
*   **Hierarchical Symbol Table (`symbol_table.py`)**: Supports nested lexical scoping, shadow warnings, uninitialized reads detection, and unused variable tracking.
*   **C Type System (`type_checker.py`)**: Enforces static type compatibility, pointer arithmetic verification, structure member accesses (`.` and `->`), and function signature argument checks.

### 3. Advanced Middle-End & Program Analysis
*   **Control Flow Graph (`cfg.py`)**: Generates function-level CFGs mapped as basic blocks containing sequential non-branching instructions.
*   **Static Call Graph (`call_graph.py`)**: Models program-wide function call edges, detects direct/mutual recursions via DFS coloring, identifies dead functions, and groups strongly connected components (SCCs) using Tarjan's algorithm.
*   **Refactoring & Reference Engine (`refactoring.py`)**: Provides scope-aware *Go-to-Definition*, *Find-All-References*, hover details (extracting attached Doxygen block comments), and *Safe Rename Refactoring* with unified diff output.

### 4. Interactive CLI REPL Console (`repl.py`)
*   Provides an interactive terminal loop to load C programs and execute advanced analysis commands dynamically.

---

## 🏆 Completed Premium Bonus Features

*   **Static Single Assignment (SSA) Form**: Translates CFGs into SSA form using Cytron's worklist algorithm to place $\phi$-functions at dominance frontiers and rename variable subscripts.
*   **Dominator Tree & Dominance Frontiers**: Computes immediate dominators (`idom`) using the mathematical **Lengauer-Tarjan** algorithm and extracts dominance frontiers.
*   **Automatic Language Detection**: A statistical heuristic classifier identifying whether an unlabeled file is C, Python, or Java based on keyword weights, colons, shebangs, and curly brace frequencies.
*   **Docker Containerization**: Containers the environment to compile, test, and run the REPL interactively on any machine with zero local setup.
*   **CI/CD Pipeline with GitHub Pages**: Runs 279 automated tests with code coverage metrics upon every commit, generating a highlighted HTML webpage of a canonical C source code deployed automatically to GitHub Pages.

---

## 📂 Project Directory Structure

```text
Compiler-Design-Project/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI/CD pipeline
├── docs/                       # Project guidelines and pdf documentation
│   ├── project_report.pdf
│   └── project_requirements.pdf
├── src/                        # Main compiler source package
│   └── cc_analyzer/
│       ├── analysis/           # Graph analysis passes (CFG, Call Graph, SSA, Dominance)
│       │   ├── call_graph.py
│       │   ├── cfg.py
│       │   ├── dominance.py
│       │   ├── language_detector.py
│       │   ├── refactoring.py
│       │   └── ssa.py
│       ├── core/               # Front-end pipeline (Lexer, Parser, AST, Tokens)
│       │   ├── ast_nodes.py
│       │   ├── lexer.py
│       │   ├── location.py
│       │   ├── parser.py
│       │   └── tokens.py
│       ├── presentation/       # CLI and UI representations (REPL, highlighter)
│       │   ├── highlighter.py  
│       │   └── repl.py         # Interactive CLI console
│       └── semantics/          # Name & Type systems (TypeChecker, Symbol Table, Intellisense)
│           ├── intellisense.py
│           ├── symbol_table.py
│           └── type_checker.py
├── tests/                      # Automated testing suite (179 tests)
│   ├── canonical_test.c        # C benchmark file for HTML page
│   ├── test_call_graph.py
│   ├── test_cfg.py
│   ├── test_dominance.py
│   ├── test_highlighter.py
│   ├── test_intellisense.py
│   ├── test_language_detector.py
│   ├── test_lexer.py
│   ├── test_parser.py
│   ├── test_refactoring.py
│   ├── test_repl.py
│   ├── test_ssa.py
│   └── test_type_checker.py
├── dockerfile                  # Docker containerization config
├── generate_report.py          # Automated HTML report generator script
├── input.c                     # Sample C input file
├── LICENSE                     # MIT License
├── main.py                     # Master compiler compilation runner script
├── pytest.ini                  # Local coverage and test configurations
├── README.md                   # Project documentation
└── requirements.txt            # Python package dependencies
```

---

## 🚀 Getting Started

### Method 1: Local Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/alikashipazha/Compiler-Design-Project.git
    cd Compiler-Design-Project
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Launch the Interactive REPL**:
    ```bash
    python -m cc_analyzer.presentation.repl
    ```

### Method 2: Running with Docker (Recommended)

1.  **Build the Container Image**:
    ```bash
    docker build -t cc-analyzer .
    ```

2.  **Run the Interactive REPL container**:
    ```bash
    docker run -it cc-analyzer
    ```

---

## 💻 REPL Console Command Guide

Once the REPL is running, you can interact with the system using these commands:

| Command | Description | Example |
| :--- | :--- | :--- |
| `load <code>` | Loads raw C source code into the active engine. | `load void main() { int x = 5; }` |
| `goto-def <line> <col>` | Returns the declaration coordinates of a symbol. | `goto-def 4 15` |
| `find-refs <line> <col>` | Locates every scope-aware usage coordinate. | `find-refs 2 9` |
| `hover <line> <col>` | Returns symbol signature and preceding Doxygen block. | `hover 3 10` |
| `rename <line> <col> <name>` | Safely renames a symbol, outputting a unified diff. | `rename 2 9 new_name` |
| `show-cfg <func>` | Displays CFG basic blocks, instructions and edges. | `show-cfg factorial` |
| `show-callgraph` | Displays program Call Graph and Tarjan's SCC groups. | `show-callgraph` |
| `show-dominators <func>` | Displays Lengauer-Tarjan idom, DT tree, and DF. | `show-dominators factorial` |
| `show-ssa <func>` | Computes and displays the Static Single Assignment form. | `show-ssa factorial` |
| `detect <code>` | Predicts source language (C/Python/Java) with % score. | `detect def f(): pass` |
| `dead-code` | Reports dead functions, unreachable blocks & unused vars. | `dead-code` |
| `diagnostics` | Prints accumulated lexical, syntactic, and semantic issues. | `diagnostics` |
| `show-ast` | Computes and displays the Abstract Syntax Tree (AST). | `show-ast` |
| `show-symboltable` | Computes and displays the Hierarchical Symbol Table & Scopes. | `show-symboltable` |
| `help` | Displays help usage information. | `help` |
| `exit` | Closes the REPL console. | `exit` |

---

## 🚀 Master Compiler Execution (main.py)

Instead of using the interactive REPL, you can run the compiler in **batch processing mode** to compile a C source file (e.g. `input.c`) and write out all intermediate compilations (tokens, syntax trees, symbol tables, and graphs) directly to disk.

### 1. Compile C Source File
Place your C subset program into a file (e.g. `input.c` at the root directory), and execute:
```bash
python main.py input.c
```

### 2. Output Artifacts Generated
Upon execution, a directory named **`output/`** will be automatically created, populated with the following physical compilations:
*   `output/tokens.txt` & `output/lexical_errors.txt`: Full token stream tables and logged lexical failures.
*   `output/syntax_errors.txt` & `output/parse_tree.txt`: Full parser recovery diagnostics and an ASCII Abstract Syntax Tree (AST).
*   `output/ast.png`: Graphical dark-themed representation of the complete AST (Section 7 - Bonus).
*   `output/semantic_errors.txt` & `output/symbol_table.txt`: Enforced C type checker issues and full hierarchical scope variables registry.
*   `output/symbol_table.png`: ID-safe, graphical dark-themed representation of Scopes and Symbol tables (Section 7 - Bonus).
*   `output/call_graph.txt` & `output/call_graph.png`: Program-wide function call adjacencies, recursions, and strongly connected components (SCCs) as both structured text and a visual dark-themed flowchart diagram.
*   `output/cfg_<function_name>.txt` & `output/cfg_<function_name>.png`: Control Flow Graph basic blocks mapped with their actual C source codes and branch/loop edges.
*   `output/dominator_tree_<function_name>.txt` & `output/dominator_tree_<function_name>.png`: Lengauer-Tarjan computed immediate dominators (`idom`) and frontiers.
*   `output/ssa_<function_name>.txt` & `output/ssa_<function_name>.png`: Full Static Single Assignment (SSA) form displaying variables renaming subscripts ($x_1, x_2$) and placed $\phi$-functions (`x_3 = phi(...)`).

---

## 🧪 Testing & Local Coverage

The project is backed by a **comprehensive suite of 179 unit and integration tests** covering every compiler pass, middle-end graph, and IDE feature.

### 1. Run All Tests
Execute `pytest` in the root directory:
```bash
python -m pytest
```

### 2. Generate Local HTML Coverage Report
Run tests with coverage. The `pytest.ini` automatically generates terminal coverage outputs and a web-based HTML report in `htmlcov/`:
```bash
pytest
```
To view the line-by-line coverage report locally in your browser, open:
```bash
# On Windows PowerShell:
start htmlcov/index.html
# On macOS/Linux:
open htmlcov/index.html
```
