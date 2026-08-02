import os
from typing import List, Optional
from cc_analyzer.core.location import SourceLocation
from cc_analyzer.semantics.symbol_table import Scope, Symbol
from cc_analyzer.core.ast_nodes import (
    ASTNode, Program, VarDecl, Param, FunctionDecl, StructDecl, Block,
    IfStmt, WhileStmt, ForStmt, ReturnStmt, ExprStmt, AssignmentExpr,
    BinaryExpr, UnaryExpr, CallExpr, ArrayAccessExpr, MemberAccessExpr,
    Identifier, IntLiteral, FloatLiteral, CharLiteral, StringLiteral
)

# Safe import of Graphviz
try:
    from graphviz import Digraph
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False


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
            self._visit(node.condition, indent + 1)
            self._visit(node.then_branch, indent + 1)
            if node.else_branch:
                self._visit(node.else_branch, indent + 1)
        elif isinstance(node, WhileStmt):
            self.lines.append(f"{prefix}WhileStmt")
            self._visit(node.condition, indent + 1)
            self._visit(node.body, indent + 1)
        elif isinstance(node, ForStmt):
            self.lines.append(f"{prefix}ForStmt")
            self._visit(node.body, indent + 1)
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
            self._visit(node.callee, indent + 1)
            for arg in node.arguments:
                self._visit(arg, indent + 1)
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


class ASTVisualizer:
    """AST Visitor that renders the entire Abstract Syntax Tree (AST) hierarchically into a PNG (Section 7 - Bonus)."""
    def __init__(self):
        self.dot: Optional[Digraph] = None
        self.node_counter = 0

    def visualize(self, node: ASTNode, output_dir: str):
        if not HAS_GRAPHVIZ:
            return
        self.dot = Digraph(name="AST", format="png")
        self.dot.attr(bgcolor="#1e1e1e", fontcolor="#ffffff")
        self.dot.attr('node', style='filled', fillcolor='#2d2d2d', color='#569cd6', fontcolor='#ffffff', fontname='Consolas', shape='box')
        self.dot.attr('edge', color='#a9a9a9')
        self.node_counter = 0
        
        self._visit(node, None)
        
        os.makedirs(output_dir, exist_ok=True)
        self.dot.render(os.path.join(output_dir, "ast"), cleanup=True)

    def _new_id(self) -> str:
        self.node_counter += 1
        return f"node_{self.node_counter}"

    def _visit(self, node: ASTNode, parent_id: Optional[str]) -> str:
        curr_id = self._new_id()
        
        label = type(node).__name__
        if isinstance(node, VarDecl):
            label = f"VarDecl\\n{node.type_spec} '{node.identifier}'"
        elif isinstance(node, FunctionDecl):
            label = f"FunctionDecl\\n{node.type_spec} {node.identifier}()"
        elif isinstance(node, StructDecl):
            label = f"StructDecl\\nstruct {node.identifier}"
        elif isinstance(node, Identifier):
            label = f"Identifier\\n'{node.name}'"
        elif isinstance(node, IntLiteral):
            label = f"IntLiteral\\n{node.raw_value}"
        elif isinstance(node, FloatLiteral):
            label = f"FloatLiteral\\n{node.raw_value}"
        elif isinstance(node, CharLiteral):
            label = f"CharLiteral\\n{node.value}"
        elif isinstance(node, StringLiteral):
            label = f"StringLiteral\\n{node.value}"
        elif isinstance(node, AssignmentExpr):
            label = f"AssignmentExpr\\n'{node.operator}'"
        elif isinstance(node, BinaryExpr):
            label = f"BinaryExpr\\n'{node.operator}'"
        elif isinstance(node, UnaryExpr):
            label = f"UnaryExpr\\n'{node.operator}'"
            
        self.dot.node(curr_id, label)
        
        if parent_id is not None:
            self.dot.edge(parent_id, curr_id)

        if isinstance(node, Program):
            for decl in node.declarations:
                self._visit(decl, curr_id)
        elif isinstance(node, VarDecl):
            if node.initializer:
                self._visit(node.initializer, curr_id)
        elif isinstance(node, FunctionDecl):
            self._visit(node.block, curr_id)
        elif isinstance(node, StructDecl):
            for m in node.members:
                self._visit(m, curr_id)
        elif isinstance(node, Block):
            for stmt in node.statements:
                self._visit(stmt, curr_id)
        elif isinstance(node, IfStmt):
            self._visit(node.condition, curr_id)
            self._visit(node.then_branch, curr_id)
            if node.else_branch:
                self._visit(node.else_branch, curr_id)
        elif isinstance(node, WhileStmt):
            self._visit(node.condition, curr_id)
            self._visit(node.body, curr_id)
        elif isinstance(node, ForStmt):
            self._visit(node.body, curr_id)
        elif isinstance(node, ReturnStmt):
            if node.expression:
                self._visit(node.expression, curr_id)
        elif isinstance(node, ExprStmt):
            if node.expression:
                self._visit(node.expression, curr_id)
        elif isinstance(node, AssignmentExpr):
            self._visit(node.target, curr_id)
            self._visit(node.value, curr_id)
        elif isinstance(node, BinaryExpr):
            self._visit(node.left, curr_id)
            self._visit(node.right, curr_id)
        elif isinstance(node, UnaryExpr):
            self._visit(node.target, curr_id)
        elif isinstance(node, CallExpr):
            self._visit(node.callee, curr_id)
            for arg in node.arguments:
                self._visit(arg, curr_id)
        elif isinstance(node, ArrayAccessExpr):
            self._visit(node.target, curr_id)
            self._visit(node.index, curr_id)
        elif isinstance(node, MemberAccessExpr):
            self._visit(node.target, curr_id)
            
        return curr_id


def _render_symbol_table_png(global_scope: Scope, output_dir: str):
    """Silently renders the hierarchical Symbol Table & Scopes into an ID-safe structured PNG inside output/."""
    if not HAS_GRAPHVIZ:
        return
    try:
        dot = Digraph(name="Symbol_Table", format="png")
        dot.attr(bgcolor="#1e1e1e", fontcolor="#ffffff", rankdir="TB")
        dot.attr('node', style='filled', fillcolor='#2d2d2d', color='#569cd6', fontcolor='#ffffff', fontname='Consolas', shape='none')
        dot.attr('edge', color='#a9a9a9', arrowhead='none')

        def build_scope_node(scope: Scope):
            # Use Python's unique object memory address id() to prevent Graphviz Node ID collisions!
            scope_id = f"scope_{id(scope)}"
            
            rows = [
                f'<tr><td colspan="3" bgcolor="#569cd6"><b><font color="#ffffff">Scope: {scope.name}</font></b></td></tr>',
                f'<tr bgcolor="#2d2d2d"><td><b><font color="#569cd6">Name</font></b></td><td><b><font color="#569cd6">Kind</font></b></td><td><b><font color="#569cd6">Type</font></b></td></tr>'
            ]
            
            for symbol in scope.symbols.values():
                rows.append(f'<tr><td><font color="#ffffff">{symbol.name}</font></td><td><font color="#4ec9b0">{symbol.kind}</font></td><td><font color="#ce9178">{symbol.type}</font></td></tr>')
                
            label_str = f'<<table border="1" cellborder="1" cellspacing="0">{"".join(rows)}</table>>'
            dot.node(scope_id, label_str)

            if scope.parent:
                parent_id = f"scope_{id(scope.parent)}"
                dot.edge(parent_id, scope_id)

            for child in scope.children:
                build_scope_node(child)

        build_scope_node(global_scope)
        dot.render(os.path.join(output_dir, "symbol_table"), cleanup=True)
    except Exception:
        pass