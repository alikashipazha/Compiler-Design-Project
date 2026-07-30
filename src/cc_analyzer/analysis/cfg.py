from typing import List, Optional, Set, Dict, Tuple
from cc_analyzer.core.location import SourceLocation
from cc_analyzer.core.ast_nodes import (
    ASTNode, VarDecl, Block, IfStmt, WhileStmt, ForStmt, ReturnStmt, ExprStmt,
    AssignmentExpr, BinaryExpr, UnaryExpr, CallExpr, Identifier, ASTNode, FunctionDecl
)

class BasicBlock:
    """Represents a Maximal sequence of non-branching statements in a CFG (Section 6.1)."""
    def __init__(self, block_id: int, label: str = ""):
        self.id = block_id
        self.label = label
        self.statements: List[ASTNode] = []
        self.successors: List['BasicBlock'] = []
        self.predecessors: List['BasicBlock'] = []

    def add_statement(self, stmt: ASTNode):
        self.statements.append(stmt)

    def link_to(self, other: 'BasicBlock'):
        """Creates a directed edge from self to other."""
        if other not in self.successors:
            self.successors.append(other)
        if self not in other.predecessors:
            other.predecessors.append(self)

    def __repr__(self) -> str:
        stmt_reprs = [type(s).__name__ for s in self.statements]
        return f"Block(id={self.id}, label='{self.label}', stmts={stmt_reprs})"


class CFG:
    """Control Flow Graph representing execution paths of a single C function."""
    def __init__(self, function_name: str):
        self.function_name = function_name
        self.entry = BasicBlock(0, "ENTRY")
        self.exit = BasicBlock(-1, "EXIT")
        self.blocks: List[BasicBlock] = [self.entry, self.exit]

    def get_reachable_blocks(self) -> Set[BasicBlock]:
        """Performs BFS from ENTRY to find all reachable basic blocks."""
        visited: Set[BasicBlock] = set()
        queue = [self.entry]
        while queue:
            curr = queue.pop(0)
            if curr not in visited:
                visited.add(curr)
                for succ in curr.successors:
                    if succ not in visited:
                        queue.append(succ)
        return visited


class CFGBuilder:
    """Constructs a CFG from a C Function body."""
    def __init__(self):
        self.block_counter = 1
        self.cfg: Optional[CFG] = None
        self.exit_block: Optional[BasicBlock] = None

    def _new_block(self, label: str = "") -> BasicBlock:
        block = BasicBlock(self.block_counter, label)
        self.block_counter += 1
        self.cfg.blocks.append(block)
        return block

    def build(self, func_name: str, body_block) -> CFG:
        self.cfg = CFG(func_name)
        self.exit_block = self.cfg.exit
        
        # If a FunctionDecl is passed, extract its internal Block (Block has .statements)
        if isinstance(body_block, FunctionDecl):
            body_block = body_block.block

        # Instantiate initial basic block after ENTRY
        first_block = self._new_block("func_start")
        self.cfg.entry.link_to(first_block)
        
        last_block = self._build_statements(body_block.statements, first_block)
        
        # Link the final block to the EXIT block if it wasn't terminated by a return
        if last_block and self.exit_block not in last_block.successors:
            last_block.link_to(self.exit_block)
            
        return self.cfg

    def _build_statements(self, statements: List[ASTNode], current_block: BasicBlock) -> Optional[BasicBlock]:
        curr = current_block
        
        for idx, stmt in enumerate(statements):
            if curr is None:
                # Statements after an unconditional return/jump are unreachable (Section 6.1.1)
                continue

            if isinstance(stmt, IfStmt):
                curr = self._build_if(stmt, curr)
            elif isinstance(stmt, WhileStmt):
                curr = self._build_while(stmt, curr)
            elif isinstance(stmt, ForStmt):
                curr = self._build_for(stmt, curr)
            elif isinstance(stmt, ReturnStmt):
                curr.add_statement(stmt)
                curr.link_to(self.exit_block)
                # Any statement textually following return inside this block is dead code
                curr = None 
            elif isinstance(stmt, Block):
                curr = self._build_statements(stmt.statements, curr)
            else:
                # Sequential non-branching statements (VarDecl, ExprStmt, Assignment)
                curr.add_statement(stmt)
                
        return curr

    def _build_if(self, node: IfStmt, current_block: BasicBlock) -> BasicBlock:
        # Branch condition is placed in the preceding block
        current_block.add_statement(node.condition)
        
        then_branch_block = self._new_block("then_branch")
        else_branch_block = self._new_block("else_branch") if node.else_branch else None
        merge_block = self._new_block("if_merge")

        current_block.link_to(then_branch_block)
        if else_branch_block:
            current_block.link_to(else_branch_block)
        else:
            current_block.link_to(merge_block)

        # Build inside branches
        then_end = self._build_statements([node.then_branch], then_branch_block)
        if then_end:
            then_end.link_to(merge_block)

        if else_branch_block and node.else_branch:
            else_end = self._build_statements([node.else_branch], else_branch_block)
            if else_end:
                else_end.link_to(merge_block)

        return merge_block

    def _build_while(self, node: WhileStmt, current_block: BasicBlock) -> BasicBlock:
        cond_block = self._new_block("while_cond")
        cond_block.add_statement(node.condition)
        
        # Link the preceding block to the loop condition
        current_block.link_to(cond_block)

        body_block = self._new_block("while_body")
        merge_block = self._new_block("while_merge")

        # Connect loop structure
        cond_block.link_to(body_block)
        cond_block.link_to(merge_block)

        body_end = self._build_statements([node.body], body_block)
        if body_end:
            body_end.link_to(cond_block)  # Loop back-edge

        return merge_block

    def _build_for(self, node: ForStmt, current_block: BasicBlock) -> BasicBlock:
        # 1. Process initializer in the current block
        if node.init:
            current_block.add_statement(node.init)

        cond_block = self._new_block("for_cond")
        if node.condition:
            cond_block.add_statement(node.condition)

        body_block = self._new_block("for_body")
        incr_block = self._new_block("for_incr")
        merge_block = self._new_block("for_merge")

        current_block.link_to(cond_block)
        cond_block.link_to(body_block)
        cond_block.link_to(merge_block)

        body_end = self._build_statements([node.body], body_block)
        if body_end:
            body_end.link_to(incr_block)

        if node.increment:
            incr_block.add_statement(node.increment)
        incr_block.link_to(cond_block)  # Loop back-edge

        return merge_block


# --- CFG-Based Static Analysis Engine ---

class CFGAnalyzer:
    """Implements graph-path based static analysis on the CFG (Section 6.1.1 & 6.5)."""
    
    @staticmethod
    def detect_unreachable_blocks(cfg: CFG) -> List[BasicBlock]:
        """Finds all blocks that have no incoming execution path from ENTRY (Unreachable Code)."""
        reachable = cfg.get_reachable_blocks()
        unreachable = []
        for block in cfg.blocks:
            if block != cfg.entry and block not in reachable:
                unreachable.append(block)
        return unreachable

    @staticmethod
    def check_definite_assignment(cfg: CFG, var_name: str, use_stmt: ASTNode) -> bool:
        """Verifies if the variable is definitely assigned on every possible path from ENTRY to its use."""
        # Find the block containing the usage of the variable
        use_block = None
        for block in cfg.blocks:
            if use_stmt in block.statements:
                use_block = block
                break

        if use_block is None:
            return True

        # Perform a Path-based reachability check to find if any path can reach 'use_block' 
        # without encountering an assignment to 'var_name'.
        # We find a path using DFS where no node on the path assigns 'var_name'.
        visited: Set[BasicBlock] = set()

        def has_uninitialized_path(curr: BasicBlock) -> bool:
            if curr == use_block:
                # Check if there is a definition inside the target block before the use
                for stmt in curr.statements:
                    if stmt == use_stmt:
                        break
                    if isinstance(stmt, AssignmentExpr) and isinstance(stmt.target, Identifier) and stmt.target.name == var_name:
                        return False # Assigned before use locally!
                return True # Uninitialized path reached the use!

            visited.add(curr)
            
            # Check if this block assigns the variable (excluding ENTRY block)
            if curr != cfg.entry:
                for stmt in curr.statements:
                    if isinstance(stmt, AssignmentExpr) and isinstance(stmt.target, Identifier) and stmt.target.name == var_name:
                        return False # Block assigns the variable, path is safe!
                    if isinstance(stmt, VarDecl) and stmt.identifier == var_name and stmt.initializer is not None:
                        return False # Initialized at declaration!

            # Continue search along successors
            for succ in curr.successors:
                if succ not in visited:
                    if has_uninitialized_path(succ):
                        return True
            return False

        return not has_uninitialized_path(cfg.entry)