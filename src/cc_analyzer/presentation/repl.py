import sys
from typing import Optional, List
from cc_analyzer.core.location import SourceLocation
from cc_analyzer.core.tokens import TokenType, Token
from cc_analyzer.core.lexer import Lexer
from cc_analyzer.core.parser import Parser
from cc_analyzer.core.ast_nodes import Program, FunctionDecl
from cc_analyzer.semantics.symbol_table import Scope, Symbol
from cc_analyzer.semantics.type_checker import TypeChecker
from cc_analyzer.analysis.cfg import CFGBuilder, CFGAnalyzer, CFG
from cc_analyzer.analysis.call_graph import CallGraph
from cc_analyzer.analysis.refactoring import RefactoringEngine

class CommandLineRepl:
    """Interactive CLI REPL for advanced compiler Middle-End operations (Section 6.6)."""
    
    def __init__(self):
        self.source: Optional[str] = None
        self.engine: Optional[RefactoringEngine] = None
        self.ast_program: Optional[Program] = None

    def run_command(self, cmd_line: str) -> str:
        """Parses and executes a single REPL command line, returning the text output."""
        cmd_line = cmd_line.strip()
        if not cmd_line:
            return ""

        parts = cmd_line.split(maxsplit=3)
        cmd = parts[0].lower()

        # Handle globally accessible commands before loading a file
        if cmd == "help":
            return self._help()
        if cmd == "exit":
            return "Exiting CC-IDE REPL."

        if cmd == "load":
            if len(parts) < 2:
                return "Error: usage: load <source_code>"
            # Re-stitch parts if source code contains spaces
            source = cmd_line[5:] # Length of "load " is 5
            self.source = source
            try:
                self.engine = RefactoringEngine(source)
                self.ast_program = self.engine.ast_program
                return f"Successfully loaded source code ({len(source)} chars)."
            except Exception as e:
                return f"Loader Error: failed to parse source code: {str(e)}"

        elif cmd == "detect":
            if len(parts) < 2: return "Error: usage: detect <source_code>"
            # Re-stitch code part if it has spaces
            code_to_detect = cmd_line[7:] # Length of "detect " is 7
            
            # Dynamic import to keep packaging clean
            from cc_analyzer.analysis.language_detector import LanguageDetector
            results = LanguageDetector.detect(code_to_detect)
            
            output = ["Language Detection Results (Statistical Classifier):"]
            for lang, conf in results:
                match_tag = " (Match)" if conf == results[0][1] and conf > 50.0 else ""
                output.append(f"  - {lang}: {conf}%{match_tag}")
            return "\n".join(output)

        # Every subsequent command requires a loaded file
        if not self.source or not self.engine or not self.ast_program:
            return "Error: No source file loaded. Run 'load <source_code>' first."

        try:
            if cmd == "goto-def":
                if len(parts) < 3: return "Error: usage: goto-def <line> <col>"
                line, col = int(parts[1]), int(parts[2])
                res = self.engine.goto_definition(line, col)
                if not res: return "Symbol not found at coordinates."
                return f"Symbol: '{res['symbol']}' ({res['kind']})\nType:   {res['type']}\nDefined: {res['defined_at']['line']}:{res['defined_at']['column']}"

            elif cmd == "find-refs":
                if len(parts) < 3: return "Error: usage: find-refs <line> <col>"
                line, col = int(parts[1]), int(parts[2])
                refs = self.engine.find_all_references(line, col)
                if not refs: return "Symbol not found or has no references."
                ref_strs = [f"{r['line']}:{r['column']}" for r in refs]
                return f"Found {len(refs)} references:\n  " + "\n  ".join(ref_strs)

            elif cmd == "hover":
                if len(parts) < 3: return "Error: usage: hover <line> <col>"
                line, col = int(parts[1]), int(parts[2])
                res = self.engine.hover(line, col)
                if not res: return "No hover information available."
                doc = f"\nDocstring: {res['documentation']}" if res['documentation'] else ""
                return f"Signature: {res['detail']} ({res['kind']}){doc}"

            elif cmd == "rename":
                if len(parts) < 4: return "Error: usage: rename <line> <col> <new_name>"
                line, col, new_name = int(parts[1]), int(parts[2]), parts[3].strip()
                diff = self.engine.rename(line, col, new_name)
                if not diff: return "Rename failed or symbol not found."
                return f"Semantics-Preserving Rename Diff:\n{diff}"

            elif cmd == "show-cfg":
                if len(parts) < 2: return "Error: usage: show-cfg <function_name>"
                func_name = parts[1]
                # Locate function decl
                func_decl = self._find_function_decl(func_name)
                if not func_decl: return f"Error: function '{func_name}' not found."
                
                builder = CFGBuilder()
                cfg = builder.build(func_name, func_decl.block)
                
                output = [f"CFG for function '{func_name}':"]
                for block in cfg.blocks:
                    succs = [str(s.id) for s in block.successors]
                    preds = [str(p.id) for p in block.predecessors]
                    output.append(f"  Block {block.id} [{block.label}]:")
                    for stmt in block.statements:
                        output.append(f"    - {type(stmt).__name__}")
                    output.append(f"    Successors:   {', '.join(succs)}")
                    output.append(f"    Predecessors: {', '.join(preds)}")
                return "\n".join(output)

            elif cmd == "show-dominators":
                if len(parts) < 2: return "Error: usage: show-dominators <function_name>"
                func_name = parts[1]
                func_decl = self._find_function_decl(func_name)
                if not func_decl: return f"Error: function '{func_name}' not found."
                
                builder = CFGBuilder()
                cfg = builder.build(func_name, func_decl.block)
                
                # Dynamic import to avoid circular dependency
                from cc_analyzer.analysis.dominance import DominanceAnalyzer
                analyzer = DominanceAnalyzer(cfg)
                analyzer.analyze()
                
                output = [f"Dominance Analysis for function '{func_name}' (Lengauer-Tarjan):"]
                output.append("  1. Immediate Dominators (idom):")
                for block in sorted(cfg.blocks, key=lambda b: b.id):
                    idom_block = analyzer.get_idom(block)
                    idom_str = f"Block {idom_block.id} [{idom_block.label}]" if idom_block else "None"
                    output.append(f"    Block {block.id} [{block.label}] -> idom: {idom_str}")
                    
                output.append("\n  2. Dominance Frontier (DF):")
                for block in sorted(cfg.blocks, key=lambda b: b.id):
                    df_blocks = sorted(list(analyzer.get_dominance_frontier(block)), key=lambda b: b.id)
                    df_str = ", ".join([f"Block {b.id}" for b in df_blocks]) if df_blocks else "None"
                    output.append(f"    DF(Block {block.id}) = {{{df_str}}}")
                    
                output.append("\n  3. Dominator Tree Structure:")
                tree = analyzer.get_dominator_tree_structure()
                
                def print_tree(curr, indent_level: int):
                    prefix = "    " * indent_level
                    output.append(f"{prefix}- Block {curr.id} [{curr.label}]")
                    for child in sorted(tree.get(curr, []), key=lambda b: b.id):
                        print_tree(child, indent_level + 1)
                        
                print_tree(cfg.entry, 1)
                return "\n".join(output)

            elif cmd == "show-ssa":
                if len(parts) < 2: return "Error: usage: show-ssa <function_name>"
                func_name = parts[1]
                func_decl = self._find_function_decl(func_name)
                if not func_decl: return f"Error: function '{func_name}' not found."
                
                builder = CFGBuilder()
                cfg = builder.build(func_name, func_decl.block)
                
                # Dynamic imports to preserve system integrity
                from cc_analyzer.analysis.dominance import DominanceAnalyzer
                from cc_analyzer.analysis.ssa import SSATransformer
                
                dom_analyzer = DominanceAnalyzer(cfg)
                dom_analyzer.analyze()
                
                transformer = SSATransformer(cfg, dom_analyzer)
                transformer.transform()
                
                output = [f"Static Single Assignment (SSA Form) for function '{func_name}':"]
                for block in sorted(cfg.blocks, key=lambda b: b.id):
                    output.append(f"  Block {block.id} [{block.label}]:")
                    
                    # 1. First, print inserted phi functions
                    phis = transformer.phi_functions.get(block, [])
                    for phi in phis:
                        output.append(f"    - {phi}")
                        
                    # 2. Then, print renamed statements
                    stmts = transformer.ssa_blocks.get(block, [])
                    for stmt in stmts:
                        output.append(f"    - {stmt}")
                        
                    succs = [str(s.id) for s in block.successors]
                    output.append(f"    Successors: {', '.join(succs)}")
                return "\n".join(output)

            elif cmd == "show-callgraph":
                cg = CallGraph()
                cg.build(self.ast_program)
                output = ["Program-Wide Call Graph:"]
                for node in sorted(cg.nodes):
                    callees = sorted(list(cg.get_callees(node)))
                    callers = sorted(list(cg.get_callers(node)))
                    recurse = " [Recursive]" if cg.is_recursive(node) else ""
                    output.append(f"  Function '{node}'{recurse}:")
                    output.append(f"    Callees: {', '.join(callees) if callees else 'None'}")
                    output.append(f"    Callers: {', '.join(callers) if callers else 'None'}")
                
                sccs = cg.get_sccs()
                output.append("\n  Strongly Connected Components (Tarjan SCCs):")
                for i, scc in enumerate(sccs):
                    output.append(f"    SCC {i+1}: {', '.join(sorted(scc))}")
                return "\n".join(output)

            elif cmd == "dead-code":
                return self._detect_dead_code()

            elif cmd == "diagnostics":
                diags = self.engine.get_diagnostics()
                if not diags:
                    return "No compiler diagnostics recorded. Perfect code!"
                output = [f"Found {len(diags)} compiler diagnostics:"]
                for d in diags:
                    output.append(f"  [{d['severity']}] Line {d['line']}, Col {d['column']}: {d['message']} (len={d['length']})")
                return "\n".join(output)

            else:
                return f"Error: Unrecognized command '{cmd}'. Type 'help' for usage."

        except ValueError as ve:
            return f"Refactoring Error: {str(ve)}"
        except Exception as e:
            return f"Command Execution Error: {str(e)}"

    def _help(self) -> str:
        return """CC-IDE REPL Interactive Command Helper:
  load <code>                    Loads C source code into the active engine.
  detect <code>                  Runs the classifier to detect C, Python, or Java with confidence %.
  goto-def <line> <col>          Jumps to the declaration site of the target identifier.
  find-refs <line> <col>         Locates every usage of the target identifier.
  hover <line> <col>             Shows variable type/function signature and attached doc comments.
  rename <line> <col> <new_name> Safely renames symbol globally producing unified diff.
  show-cfg <func>                Constructs and displays the Control Flow Graph of a function.
  show-dominators <func>         Computes and displays the Lengauer-Tarjan Dominator Tree & DF.
  show-ssa <func>                Computes and displays the Static Single Assignment (SSA) form.
  show-callgraph                 Constructs and displays the program-wide Call Graph.
  dead-code                      Detects dead functions, unreachable blocks, unused vars & uninit reads.
  diagnostics                    Prints all accumulated lexical, syntactic, and semantic diagnostics.
  help                           Shows this helper usage information.
  exit                           Exits the line loop."""

    def _find_function_decl(self, name: str) -> Optional[FunctionDecl]:
        for decl in self.ast_program.declarations:
            if isinstance(decl, FunctionDecl) and decl.identifier == name:
                return decl
        return None

    def _detect_dead_code(self) -> str:
        output = ["Program-Wide Dead Code Report (Section 6.5):"]
        
        # 1. Dead Functions from Call Graph
        cg = CallGraph()
        cg.build(self.ast_program)
        dead_funcs = sorted(list(cg.get_dead_functions()))
        output.append("  1. Dead Functions (Unreachable from 'main'):")
        if dead_funcs:
            for f in dead_funcs:
                output.append(f"    - '{f}' never called.")
        else:
            output.append("    No dead functions detected.")

        # 2. Unreachable Blocks per function CFG
        output.append("\n  2. Unreachable Basic Blocks (CFG):")
        has_unreachable_blocks = False
        builder = CFGBuilder()
        for decl in self.ast_program.declarations:
            if isinstance(decl, FunctionDecl):
                cfg = builder.build(decl.identifier, decl.block)
                unreachable = CFGAnalyzer.detect_unreachable_blocks(cfg)
                if unreachable:
                    has_unreachable_blocks = True
                    output.append(f"    Inside function '{decl.identifier}':")
                    for b in unreachable:
                        output.append(f"      - Block {b.id} [{b.label}] is unreachable.")
        if not has_unreachable_blocks:
            output.append("    No unreachable basic blocks detected.")

        # 3. Diagnostics (Unused variables & uninitialized uses from Semantics pass)
        diags = self.engine.get_diagnostics()
        
        output.append("\n  3. Unused Variables (Semantic Analysis):")
        unused_vars = [d for d in diags if d["severity"] == "Info" and "never read" in d["message"]]
        if unused_vars:
            for uv in unused_vars:
                output.append(f"    - Line {uv['line']}: {uv['message']}.")
        else:
            output.append("    No unused variables detected.")

        output.append("\n  4. Uninitialized Reads (Definite Assignment):")
        uninit_reads = [d for d in diags if d["severity"] == "Warning" and "uninitialized" in d["message"]]
        if uninit_reads:
            for ur in uninit_reads:
                output.append(f"    - Line {ur['line']}: {ur['message']}.")
        else:
            output.append("    No uninitialized variable reads detected.")

        return "\n".join(output)

    def interactive_loop(self):
        """Standard line reading loop for terminal execution."""
        print("Welcome to CC-IDE Middle-End interactive REPL console!")
        print("Type 'help' for valid commands. Press Ctrl+D/Ctrl+C or type 'exit' to quit.\n")
        
        while True:
            try:
                line = input("cc-analyzer> ")
                if not line.strip():
                    continue
                out = self.run_command(line)
                if out:
                    print(out)
                if line.strip().lower() == "exit":
                    break
            except (KeyboardInterrupt, EOFError):
                print("\nExiting CC-IDE REPL.")
                break