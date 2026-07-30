# Compiler Design Project

This repository contains the implementation of the compiler design project for the Compiler Design course at the **Faculty of Computer Engineering**, **K. N. Toosi University of Technology**.

* **Semester:** Spring Semester 1404–1405
* **Instructor:** Dr. Alaeiyan

> ## Team Members
> * **Ali Kashi Pazha** (Student ID: `40224641`)
> * **Mohammad Izadi Moghadam** (Student ID: `40215233`)

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
*   **CI/CD Pipeline with GitHub Pages**: Runs 79 automated tests with code coverage metrics upon every commit, generating a highlighted HTML webpage of a canonical C source code deployed automatically to GitHub Pages.

---

## 📂 Project Directory Structure

```text
Compiler-Design-Project/
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI/CD pipeline
├── src/
│   └── cc_analyzer/
│       ├── core/
│       │   ├── location.py    # Line and column tracking
│       │   ├── tokens.py      # TokenType definitions & Token class
│       │   ├── lexer.py       # Hand-written DFA Lexical Analyzer
│       │   ├── ast_nodes.py   # Complete OOP AST Node classes
│       │   └── parser.py      # LL(k) Recursive-Descent Parser
│       ├── semantics/
│       │   ├── symbol_table.py# Hierarchical lexical scopes
│       │   ├── type_checker.py# C-type system visitor
│       │   └── intellisense.py# Hover, completion & diagnostics
│       ├── analysis/
│       │   ├── cfg.py         # Basic block & CFG construction
│       │   ├── call_graph.py  # Call graph & Tarjan SCCs
│       │   ├── dominance.py   # Lengauer-Tarjan Dominator Tree
│       │   ├── ssa.py         # Cytron SSA & Phi placements
│       │   └── refactoring.py # Go-to-def, refs & Safe Rename
│       └── presentation/
│           ├── highlighter.py # ANSI/HTML syntax highlighter
│           └── repl.py        # Interactive CLI console
├── tests/                     # Comprehensive test suites (79 tests)
│   ├── canonical_test.c       # C benchmark file for HTML page
│   └── test_*.py              # pytest modules
├── generate_report.py         # Automated HTML report generator script
├── pytest.ini                 # Local coverage and test configurations
├── requirements.txt           # Python package dependencies
└── Dockerfile                 # Multi-stage lightweight Docker image
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
| `help` | Displays help usage information. | `help` |
| `exit` | Closes the REPL console. | `exit` |

---

## 🧪 Testing & Local Coverage

The project is backed by a **comprehensive suite of 79 unit and integration tests** covering every compiler pass, middle-end graph, and IDE feature.

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
```
```