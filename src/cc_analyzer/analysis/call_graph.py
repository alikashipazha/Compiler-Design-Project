from typing import Dict, List, Optional, Set, Tuple
from cc_analyzer.core.ast_nodes import (
    ASTNode, Program, VarDecl, Param, FunctionDecl, StructDecl, Block,
    IfStmt, WhileStmt, ForStmt, ReturnStmt, ExprStmt, AssignmentExpr,
    BinaryExpr, UnaryExpr, CallExpr, ArrayAccessExpr, MemberAccessExpr,
    Identifier, IntLiteral, FloatLiteral, CharLiteral, StringLiteral
)

class CallSiteExtractor:
    """Lightweight AST Visitor to collect all called function identifiers within a block."""
    def __init__(self):
        self.callees: Set[str] = set()

    def extract(self, node: ASTNode) -> Set[str]:
        self.callees.clear()
        node.accept(self)
        return self.callees

    # --- Visitor Traversal Methods ---

    def visit_program(self, node: Program):
        for decl in node.declarations:
            decl.accept(self)

    def visit_var_decl(self, node: VarDecl):
        if node.initializer:
            node.initializer.accept(self)

    def visit_param(self, node: Param):
        pass

    def visit_function_decl(self, node: FunctionDecl):
        node.block.accept(self)

    def visit_struct_decl(self, node: StructDecl):
        pass

    def visit_block(self, node: Block):
        for stmt in node.statements:
            stmt.accept(self)

    def visit_if_stmt(self, node: IfStmt):
        node.condition.accept(self)
        node.then_branch.accept(self)
        if node.else_branch:
            node.else_branch.accept(self)

    def visit_while_stmt(self, node: WhileStmt):
        node.condition.accept(self)
        node.body.accept(self)

    def visit_for_stmt(self, node: ForStmt):
        if node.init:
            node.init.accept(self)
        if node.condition:
            node.condition.accept(self)
        if node.increment:
            node.increment.accept(self)
        node.body.accept(self)

    def visit_return_stmt(self, node: ReturnStmt):
        if node.expression:
            node.expression.accept(self)

    def visit_expr_stmt(self, node: ExprStmt):
        if node.expression:
            node.expression.accept(self)

    def visit_assignment_expr(self, node: AssignmentExpr):
        node.target.accept(self)
        node.value.accept(self)

    def visit_binary_expr(self, node: BinaryExpr):
        node.left.accept(self)
        node.right.accept(self)

    def visit_unary_expr(self, node: UnaryExpr):
        node.target.accept(self)

    def visit_call_expr(self, node: CallExpr):
        if isinstance(node.callee, Identifier):
            self.callees.add(node.callee.name)
        else:
            node.callee.accept(self)
        for arg in node.arguments:
            arg.accept(self)

    def visit_array_access_expr(self, node: ArrayAccessExpr):
        node.target.accept(self)
        node.index.accept(self)

    def visit_member_access_expr(self, node: MemberAccessExpr):
        node.target.accept(self)

    def visit_identifier(self, node: Identifier):
        pass

    def visit_int_literal(self, node: IntLiteral):
        pass
    def visit_float_literal(self, node: FloatLiteral):
        pass
    def visit_char_literal(self, node: CharLiteral):
        pass
    def visit_string_literal(self, node: StringLiteral):
        pass


class CallGraph:
    """Program-wide static call graph builder and query engine (Section 6.2)."""
    
    def __init__(self):
        self.nodes: Set[str] = set()                            # All function names
        self.adjacency_list: Dict[str, Set[str]] = {}           # f -> [callees]
        self.reverse_adjacency_list: Dict[str, Set[str]] = {}   # f -> [callers]

    def build(self, program: Program):
        """Constructs the call graph by scanning function declarations and their bodies."""
        self.nodes.clear()
        self.adjacency_list.clear()
        self.reverse_adjacency_list.clear()

        # Step 1: Collect all defined functions as graph nodes
        functions_map: Dict[str, FunctionDecl] = {}
        for decl in program.declarations:
            if isinstance(decl, FunctionDecl):
                self.nodes.add(decl.identifier)
                self.adjacency_list[decl.identifier] = set()
                self.reverse_adjacency_list[decl.identifier] = set()
                functions_map[decl.identifier] = decl

        # Step 2: Traverse bodies to extract called functions (Edges)
        extractor = CallSiteExtractor()
        for func_name, func_decl in functions_map.items():
            called_funcs = extractor.extract(func_decl.block)
            for callee in called_funcs:
                # We register the edge only if the callee is a defined function in our program
                if callee in self.nodes:
                    self.adjacency_list[func_name].add(callee)
                    self.reverse_adjacency_list[callee].add(func_name)

    # --- Call Graph Queries (Section 6.2.1) ---

    def get_callees(self, func_name: str) -> Set[str]:
        """Returns the direct callees of function f."""
        return self.adjacency_list.get(func_name, set())

    def get_callers(self, func_name: str) -> Set[str]:
        """Returns the direct callers of function f."""
        return self.reverse_adjacency_list.get(func_name, set())

    def get_transitive_callees(self, func_name: str) -> Set[str]:
        """Performs BFS to find all transitively reachable callees from f."""
        if func_name not in self.nodes:
            return set()
        visited: Set[str] = set()
        queue = [func_name]
        while queue:
            curr = queue.pop(0)
            if curr not in visited:
                if curr != func_name:  # Exclude self unless reachable recursively
                    visited.add(curr)
                for succ in self.get_callees(curr):
                    if succ not in visited:
                        queue.append(succ)
        return visited

    def get_transitive_callers(self, func_name: str) -> Set[str]:
        """Performs BFS on the reversed graph to find all transitively reaching callers of f."""
        if func_name not in self.nodes:
            return set()
        visited: Set[str] = set()
        queue = [func_name]
        while queue:
            curr = queue.pop(0)
            if curr not in visited:
                if curr != func_name:
                    visited.add(curr)
                for pred in self.get_callers(curr):
                    if pred not in visited:
                        queue.append(pred)
        return visited

    def is_recursive(self, func_name: str) -> bool:
        """Detects whether a function is recursive (direct or mutual) using DFS cycle detection."""
        if func_name not in self.nodes:
            return False
            
        # 3-color DFS marking: 0 = unvisited, 1 = visiting, 2 = visited
        colors: Dict[str, int] = {node: 0 for node in self.nodes}

        def has_cycle(curr: str) -> bool:
            colors[curr] = 1  # Gray (visiting)
            for succ in self.get_callees(curr):
                if colors[succ] == 1:
                    # We hit a visiting node -> Cycle found!
                    # For a specific function, we only care if that function is part of the cycle
                    if succ == func_name or curr == func_name:
                        return True
                elif colors[succ] == 0:
                    if has_cycle(succ):
                        return True
            colors[curr] = 2  # Black (visited)
            return False

        return has_cycle(func_name)

    def get_dead_functions(self) -> Set[str]:
        """Finds all defined functions that are not transitively reachable from 'main'."""
        if "main" not in self.nodes:
            # If main doesn't exist, we assume all defined functions are dead/unreachable
            return self.nodes.copy()
            
        reachable_from_main = self.get_transitive_callees("main")
        reachable_from_main.add("main")  # main is naturally alive
        
        return self.nodes - reachable_from_main

    def get_sccs(self) -> List[List[str]]:
        """Finds all Strongly Connected Components (SCCs) using Tarjan's algorithm."""
        index_counter = 0
        indices: Dict[str, int] = {}
        lowlink: Dict[str, int] = {}
        stack: List[str] = []
        on_stack: Set[str] = set()
        sccs: List[List[str]] = []

        def strongconnect(node: str):
            nonlocal index_counter
            indices[node] = index_counter
            lowlink[node] = index_counter
            index_counter += 1
            stack.append(node)
            on_stack.add(node)

            for successor in self.get_callees(node):
                if successor not in indices:
                    # Successor has not yet been visited; recurse on it
                    strongconnect(successor)
                    lowlink[node] = min(lowlink[node], lowlink[successor])
                elif successor in on_stack:
                    # Successor is in the current SCC stack, hence in the current DFS path
                    lowlink[node] = min(lowlink[node], indices[successor])

            # If node is a root node, pop the stack and generate an SCC
            if lowlink[node] == indices[node]:
                scc = []
                while True:
                    successor = stack.pop()
                    on_stack.remove(successor)
                    scc.append(successor)
                    if successor == node:
                        break
                sccs.append(scc)

        for node in self.nodes:
            if node not in indices:
                strongconnect(node)
                
        return sccs