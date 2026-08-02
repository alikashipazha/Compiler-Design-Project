import os
import sys
from typing import List

# Safe import of Graphviz to ensure 100% stability
try:
    from graphviz import Digraph
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

# Set path configuration so python can resolve our core packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from cc_analyzer.core.location import SourceLocation
from cc_analyzer.core.tokens import TokenType, Token
from cc_analyzer.core.lexer import Lexer
from cc_analyzer.core.parser import Parser
from cc_analyzer.semantics.symbol_table import Scope, Symbol
from cc_analyzer.semantics.type_checker import TypeChecker
from cc_analyzer.analysis.cfg import CFGBuilder, CFG, BasicBlock
from cc_analyzer.analysis.call_graph import CallGraph
from cc_analyzer.analysis.dominance import DominanceAnalyzer
from cc_analyzer.analysis.ssa import SSATransformer
from cc_analyzer.core.ast_nodes import (
    ASTNode, Program, VarDecl, Param, FunctionDecl, StructDecl, Block,
    IfStmt, WhileStmt, ForStmt, ReturnStmt, ExprStmt, AssignmentExpr,
    BinaryExpr, UnaryExpr, CallExpr, ArrayAccessExpr, MemberAccessExpr,
    Identifier, IntLiteral, FloatLiteral, CharLiteral, StringLiteral
)

class ASTPrinter:
    """Helper Visitor to format the AST into a beautiful indented ASCII Tree Representation."""
    def __init__(self):
        self.lines: List[str] = []

    def print_node(self, node: ASTNode) -> str:
        self.lines.clear()
        self._visit(node, 0)
        return "\n".join(self.lines)

    def _visit(self, node: ASTNode, indent: int):
        prefix = "  " * indent
        
        if isinstance(node, Program):
            self.lines.append(f"{prefix}Program")
            for decl in node.declarations:
                self._visit(decl, indent + 1)
        elif isinstance(node, VarDecl):
            init_str = " (with initializer)" if node.initializer else ""
            self.lines.append(f"{prefix}VarDecl: {node.type_spec} '{node.identifier}'{init_str}")
            if node.initializer:
                self._visit(node.initializer, indent + 1)
        elif isinstance(node, FunctionDecl):
            self.lines.append(f"{prefix}FunctionDecl: {node.type_spec} {node.identifier}()")
            for p in node.params:
                self.lines.append(f"{prefix}  - Param: {p.type_spec} '{p.identifier}'")
            self._visit(node.block, indent + 1)
        elif isinstance(node, StructDecl):
            self.lines.append(f"{prefix}StructDecl: struct {node.identifier}")
            for m in node.members:
                self._visit(m, indent + 1)
        elif isinstance(node, Block):
            self.lines.append(f"{prefix}Block")
            for stmt in node.statements:
                self._visit(stmt, indent + 1)
        elif isinstance(node, IfStmt):
            self.lines.append(f"{prefix}IfStmt")
            self.lines.append(f"{prefix}  Condition:")
            self._visit(node.condition, indent + 2)
            self.lines.append(f"{prefix}  Then:")
            self._visit(node.then_branch, indent + 2)
            if node.else_branch:
                self.lines.append(f"{prefix}  Else:")
                self._visit(node.else_branch, indent + 2)
        elif isinstance(node, WhileStmt):
            self.lines.append(f"{prefix}WhileStmt")
            self.lines.append(f"{prefix}  Condition:")
            self._visit(node.condition, indent + 2)
            self.lines.append(f"{prefix}  Body:")
            self._visit(node.body, indent + 2)
        elif isinstance(node, ForStmt):
            self.lines.append(f"{prefix}ForStmt")
            if node.init:
                self.lines.append(f"{prefix}  Init:")
                self._visit(node.init, indent + 2)
            if node.condition:
                self.lines.append(f"{prefix}  Condition:")
                self._visit(node.condition, indent + 2)
            if node.increment:
                self.lines.append(f"{prefix}  Increment:")
                self._visit(node.increment, indent + 2)
            self.lines.append(f"{prefix}  Body:")
            self._visit(node.body, indent + 2)
        elif isinstance(node, ReturnStmt):
            self.lines.append(f"{prefix}ReturnStmt")
            if node.expression:
                self._visit(node.expression, indent + 1)
        elif isinstance(node, ExprStmt):
            self.lines.append(f"{prefix}ExprStmt")
            if node.expression:
                self._visit(node.expression, indent + 1)
        elif isinstance(node, AssignmentExpr):
            self.lines.append(f"{prefix}AssignmentExpr (op: '{node.operator}')")
            self._visit(node.target, indent + 1)
            self._visit(node.value, indent + 1)
        elif isinstance(node, BinaryExpr):
            self.lines.append(f"{prefix}BinaryExpr (op: '{node.operator}')")
            self._visit(node.left, indent + 1)
            self._visit(node.right, indent + 1)
        elif isinstance(node, UnaryExpr):
            self.lines.append(f"{prefix}UnaryExpr (op: '{node.operator}')")
            self._visit(node.target, indent + 1)
        elif isinstance(node, CallExpr):
            self.lines.append(f"{prefix}CallExpr")
            self.lines.append(f"{prefix}  Callee:")
            self._visit(node.callee, indent + 2)
            if node.arguments:
                self.lines.append(f"{prefix}  Arguments:")
                for arg in node.arguments:
                    self._visit(arg, indent + 3)
        elif isinstance(node, ArrayAccessExpr):
            self.lines.append(f"{prefix}ArrayAccessExpr")
            self._visit(node.target, indent + 1)
            self._visit(node.index, indent + 1)
        elif isinstance(node, MemberAccessExpr):
            self.lines.append(f"{prefix}MemberAccessExpr (op: '{node.operator}{node.member}')")
            self._visit(node.target, indent + 1)
        elif isinstance(node, Identifier):
            self.lines.append(f"{prefix}Identifier: '{node.name}'")
        elif isinstance(node, IntLiteral):
            self.lines.append(f"{prefix}IntLiteral: {node.raw_value}")
        elif isinstance(node, FloatLiteral):
            self.lines.append(f"{prefix}FloatLiteral: {node.raw_value}")
        elif isinstance(node, CharLiteral):
            self.lines.append(f"{prefix}CharLiteral: {node.value}")
        elif isinstance(node, StringLiteral):
            self.lines.append(f"{prefix}StringLiteral: {node.value}")


def print_scope_tree_to_lines(scope: Scope, lines: List[str], indent: int = 0):
    """Recursively dumps the Scope Hierarchical Tree into formatted string lines."""
    prefix = "  " * indent
    lines.append(f"{prefix}Scope: {scope.name}")
    for symbol in scope.symbols.values():
        sig = f" {symbol.signature}" if symbol.signature else ""
        lines.append(f"{prefix}  [{symbol.kind}] '{symbol.name}' : {symbol.type}{sig} (def: {symbol.definition_loc})")
    for child in scope.children:
        print_scope_tree_to_lines(child, lines, indent + 1)


# --- Visual Drawing Helpers for main.py (Section 7 - Bonus) ---

def _render_cfg_png(cfg: CFG, output_dir: str):
    try:
        dot = Digraph(name=f"CFG_{cfg.function_name}", format="png")
        dot.attr(bgcolor="#1e1e1e", fontcolor="#ffffff", rankdir="TB")
        dot.attr('node', style='filled', fillcolor='#2d2d2d', color='#569cd6', fontcolor='#ffffff', fontname='Consolas', shape='box')
        dot.attr('edge', color='#a9a9a9', fontcolor='#a9a9a9', fontname='Consolas')

        dot.node("ENTRY", "ENTRY", fillcolor="#1e1e1e", color="#569cd6")
        dot.node("EXIT", "EXIT", fillcolor="#1e1e1e", color="#569cd6")

        for block in cfg.blocks:
            if block.id in (0, -1):
                continue
            label_parts = [f"Block {block.id} [{block.label}]"]
            for stmt in block.statements:
                label_parts.append(f"- {type(stmt).__name__}")
            dot.node(str(block.id), "\\n".join(label_parts))

        for block in cfg.blocks:
            src_id = "ENTRY" if block.id == 0 else ("EXIT" if block.id == -1 else str(block.id))
            for succ in block.successors:
                dst_id = "ENTRY" if succ.id == 0 else ("EXIT" if succ.id == -1 else str(succ.id))
                dot.edge(src_id, dst_id)

        dot.render(os.path.join(output_dir, f"cfg_{cfg.function_name}"), cleanup=True)
    except Exception:
        pass

def _render_dominators_png(cfg: CFG, analyzer, output_dir: str):
    try:
        dot = Digraph(name=f"DOM_{cfg.function_name}", format="png")
        dot.attr(bgcolor="#1e1e1e", fontcolor="#ffffff", rankdir="TB")
        dot.attr('node', style='filled', fillcolor='#2d2d2d', color='#569cd6', fontcolor='#ffffff', fontname='Consolas', shape='box')
        dot.attr('edge', color='#a9a9a9', fontcolor='#a9a9a9', fontname='Consolas')

        for block in cfg.blocks:
            label = f"Block {block.id}\\n[{block.label}]"
            dot.node(str(block.id), label)

        tree = analyzer.get_dominator_tree_structure()
        for parent, children in tree.items():
            for child in children:
                dot.edge(str(parent.id), str(child.id))

        dot.render(os.path.join(output_dir, f"dominator_tree_{cfg.function_name}"), cleanup=True)
    except Exception:
        pass

def _render_ssa_png(cfg: CFG, transformer, output_dir: str):
    try:
        dot = Digraph(name=f"SSA_{cfg.function_name}", format="png")
        dot.attr(bgcolor="#1e1e1e", fontcolor="#ffffff", rankdir="TB")
        dot.attr('node', style='filled', fillcolor='#2d2d2d', color='#569cd6', fontcolor='#ffffff', fontname='Consolas', shape='box')
        dot.attr('edge', color='#a9a9a9', fontcolor='#a9a9a9', fontname='Consolas')

        dot.node("ENTRY", "ENTRY", fillcolor="#1e1e1e", color="#569cd6")
        dot.node("EXIT", "EXIT", fillcolor="#1e1e1e", color="#569cd6")

        for block in cfg.blocks:
            if block.id in (0, -1):
                continue
            label_parts = [f"Block {block.id} [{block.label}]"]
            for phi in transformer.phi_functions.get(block, []):
                label_parts.append(f"- {phi}")
            for stmt in transformer.ssa_blocks.get(block, []):
                label_parts.append(f"- {stmt}")
            dot.node(str(block.id), "\\n".join(label_parts))

        for block in cfg.blocks:
            src_id = "ENTRY" if block.id == 0 else ("EXIT" if block.id == -1 else str(block.id))
            for succ in block.successors:
                dst_id = "ENTRY" if succ.id == 0 else ("EXIT" if succ.id == -1 else str(succ.id))
                dot.edge(src_id, dst_id)

        dot.render(os.path.join(output_dir, f"ssa_{cfg.function_name}"), cleanup=True)
    except Exception:
        pass

def _render_call_graph_png(cg: CallGraph, output_dir: str):
    try:
        dot = Digraph(name="Call_Graph", format="png")
        dot.attr(bgcolor="#1e1e1e", fontcolor="#ffffff")
        dot.attr('node', style='filled', fillcolor='#2d2d2d', color='#569cd6', fontcolor='#ffffff', fontname='Consolas', shape='box')
        dot.attr('edge', color='#a9a9a9', fontcolor='#a9a9a9', fontname='Consolas')

        for node in cg.nodes:
            color = "#dcdcaa" if cg.is_recursive(node) else "#569cd6"
            label = f"{node} [Recursive]" if cg.is_recursive(node) else node
            dot.node(node, label, color=color)

        for node in cg.nodes:
            for callee in cg.get_callees(node):
                dot.edge(node, callee)

        dot.render(os.path.join(output_dir, "call_graph"), cleanup=True)
    except Exception:
        pass


def main():
    # Determine the input source file (defaults to input.c)
    input_file = sys.argv[1] if len(sys.argv) > 1 else "input.c"
    output_dir = "output"

    if not os.path.exists(input_file):
        print(f"Error: Input C source file '{input_file}' not found.")
        print("Please create an 'input.c' file in the root directory first.")
        sys.exit(1)

    print(f"Processing input file: '{input_file}'...")
    with open(input_file, "r", encoding="utf-8") as f:
        source_code = f.read()

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # ==========================================
    # PHASE 1: LEXICAL ANALYSIS
    # ==========================================
    print("Executing Lexical Analysis...")
    lexer = Lexer(source_code)
    all_tokens = lexer.tokenize(keep_comments=True)
    
    # 1.1 Output tokens.txt
    with open(os.path.join(output_dir, "tokens.txt"), "w", encoding="utf-8") as f:
        f.write(f"Scanned {len(all_tokens)} tokens (including comments):\n")
        for token in all_tokens:
            if token.type != TokenType.EOF:
                f.write(f"  Line {token.location.line}, Col {token.location.column} | {token.type.name} : '{token.lexeme}' (span: {token.start_pos}:{token.end_pos})\n")

    # 1.2 Output lexical_errors.txt
    lexical_errors = [t for t in all_tokens if t.type == TokenType.INVALID]
    with open(os.path.join(output_dir, "lexical_errors.txt"), "w", encoding="utf-8") as f:
        if lexical_errors:
            f.write(f"Found {len(lexical_errors)} lexical errors:\n")
            for err in lexical_errors:
                f.write(f"  Line {err.location.line}, Col {err.location.column} : Invalid lexeme '{err.lexeme}'\n")
        else:
            f.write("No lexical errors recorded. Clean tokenization!")

    # ==========================================
    # PHASE 2: SYNTACTIC ANALYSIS
    # ==========================================
    print("Executing Syntactic Analysis...")
    # Tokens without comments for the parser
    parser_tokens = [t for t in all_tokens if t.type not in (TokenType.COMMENT_SINGLE, TokenType.COMMENT_BLOCK)]
    parser = Parser(parser_tokens)
    ast_program = parser.parse()

    # 2.1 Output syntax_errors.txt
    with open(os.path.join(output_dir, "syntax_errors.txt"), "w", encoding="utf-8") as f:
        if parser.errors:
            f.write(f"Found {len(parser.errors)} syntax errors during parsing:\n")
            for err in parser.errors:
                f.write(f"  - {err}\n")
        else:
            f.write("No syntax errors. Parsing succeeded!")

    # 2.2 Output parse_tree.txt (ASCII representation of AST)
    with open(os.path.join(output_dir, "parse_tree.txt"), "w", encoding="utf-8") as f:
        if ast_program:
            printer = ASTPrinter()
            f.write(printer.print_node(ast_program))
        else:
            f.write("Parse tree could not be generated (empty program or parse crashed).")

    # ==========================================
    # PHASE 3: SEMANTIC ANALYSIS
    # ==========================================
    print("Executing Semantic Analysis & Type Checking...")
    type_checker = TypeChecker()
    semantic_diagnostics = []
    if ast_program:
        type_checker.check(ast_program)
        semantic_diagnostics = type_checker.diagnostics

    # 3.1 Output semantic_errors.txt
    with open(os.path.join(output_dir, "semantic_errors.txt"), "w", encoding="utf-8") as f:
        if semantic_diagnostics:
            f.write(f"Found {len(semantic_diagnostics)} semantic diagnostics:\n")
            for d in semantic_diagnostics:
                f.write(f"  [{d['severity']}] Line {d['line']}, Col {d['column']}: {d['message']} (lexeme width: {d['length']})\n")
        else:
            f.write("No semantic errors. Type checking succeeded!")

    # 3.2 Output symbol_table.txt
    with open(os.path.join(output_dir, "symbol_table.txt"), "w", encoding="utf-8") as f:
        scope_lines = []
        print_scope_tree_to_lines(type_checker.global_scope, scope_lines)
        f.write("\n".join(scope_lines))

    # ==========================================
    # PHASE 4: ADVANCED GRAPHS & SSA FORM
    # ==========================================
    if ast_program:
        print("Executing Program-Wide Graph & Middle-End SSA Analyses...")
        
        # 4.1 Program Call Graph -> call_graph.txt
        cg = CallGraph()
        cg.build(ast_program)
        with open(os.path.join(output_dir, "call_graph.txt"), "w", encoding="utf-8") as f:
            f.write("Program-Wide Call Graph Analysis:\n")
            for node in sorted(cg.nodes):
                recurse = " [Recursive]" if cg.is_recursive(node) else ""
                f.write(f"  Function: '{node}'{recurse}\n")
                f.write(f"    Direct Callees: {', '.join(sorted(list(cg.get_callees(node)))) or 'None'}\n")
                f.write(f"    Direct Callers: {', '.join(sorted(list(cg.get_callers(node)))) or 'None'}\n")
            
            sccs = cg.get_sccs()
            f.write("\nStrongly Connected Components (Tarjan's SCCs):\n")
            for i, scc in enumerate(sccs):
                f.write(f"  SCC {i+1}: {', '.join(sorted(scc))}\n")
                
            dead_funcs = cg.get_dead_functions()
            f.write("\nDead Functions (Not reachable from 'main'):\n")
            if dead_funcs:
                for df in sorted(list(dead_funcs)):
                    f.write(f"  - '{df}' is dead code.\n")
            else:
                f.write("  No dead functions detected.\n")

        # Render physical Call Graph PNG representation (Section 7 - Bonus)
        if HAS_GRAPHVIZ:
            _render_call_graph_png(cg, output_dir)

        # 4.2 Function-level CFGs and SSA form
        cfg_builder = CFGBuilder()
        for decl in ast_program.declarations:
            if isinstance(decl, FunctionDecl):
                func_name = decl.identifier
                
                # Build CFG -> cfg_<function_name>.txt
                cfg = cfg_builder.build(func_name, decl)
                with open(os.path.join(output_dir, f"cfg_{func_name}.txt"), "w", encoding="utf-8") as f:
                    f.write(f"Control Flow Graph (CFG) for function '{func_name}':\n")
                    for block in sorted(cfg.blocks, key=lambda b: b.id):
                        f.write(f"  Block {block.id} [{block.label}]:\n")
                        for stmt in block.statements:
                            f.write(f"    - {type(stmt).__name__}\n")
                        f.write(f"    Successors:   {', '.join([str(s.id) for s in block.successors]) or 'None'}\n")
                        f.write(f"    Predecessors: {', '.join([str(p.id) for p in block.predecessors]) or 'None'}\n")

                # Build SSA -> ssa_<function_name>.txt
                dom_analyzer = DominanceAnalyzer(cfg)
                dom_analyzer.analyze()
                
                ssa_transformer = SSATransformer(cfg, dom_analyzer)
                ssa_transformer.transform()
                
                with open(os.path.join(output_dir, f"ssa_{func_name}.txt"), "w", encoding="utf-8") as f:
                    f.write(f"Static Single Assignment (SSA Form) for function '{func_name}':\n")
                    for block in sorted(cfg.blocks, key=lambda b: b.id):
                        f.write(f"  Block {block.id} [{block.label}]:\n")
                        # 1. Print Phi functions
                        for phi in ssa_transformer.phi_functions.get(block, []):
                            f.write(f"    - {phi}\n")
                        # 2. Print Renamed Statements
                        for stmt in ssa_transformer.ssa_blocks.get(block, []):
                            f.write(f"    - {stmt}\n")
                        f.write(f"    Successors: {', '.join([str(s.id) for s in block.successors]) or 'None'}\n")

                # Render physical CFG, Dominator Tree, and SSA PNG representations (Section 7 - Bonus)
                if HAS_GRAPHVIZ:
                    _render_cfg_png(cfg, output_dir)
                    _render_dominators_png(cfg, dom_analyzer, output_dir)
                    _render_ssa_png(cfg, ssa_transformer, output_dir)

    print(f"\nCompilation and Middle-End analysis complete! All logs successfully generated inside directory '{output_dir}/'.")

if __name__ == "__main__":
    main()