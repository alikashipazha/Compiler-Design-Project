from typing import Dict, List, Optional, Set, Tuple
from cc_analyzer.analysis.cfg import CFG, BasicBlock
from cc_analyzer.analysis.dominance import DominanceAnalyzer
from cc_analyzer.core.ast_nodes import (
    ASTNode, VarDecl, Param, Block, ReturnStmt, ExprStmt, AssignmentExpr,
    BinaryExpr, UnaryExpr, CallExpr, ArrayAccessExpr, MemberAccessExpr,
    Identifier, IntLiteral, FloatLiteral, CharLiteral, StringLiteral
)

class SSAFormatter:
    """AST Visitor that formats expressions into SSA string representations with active subscripts."""
    
    def __init__(self, active_subscripts: Dict[str, int]):
        self.subscripts = active_subscripts

    def format_node(self, node: ASTNode) -> str:
        return node.accept(self)

    # --- Visitor Formatting Methods ---

    def visit_program(self, node): pass
    def visit_param(self, node): pass
    def visit_function_decl(self, node): pass
    def visit_struct_decl(self, node): pass
    def visit_block(self, node): pass
    def visit_if_stmt(self, node): pass
    def visit_while_stmt(self, node): pass
    def visit_for_stmt(self, node): pass

    def visit_var_decl(self, node: VarDecl) -> str:
        sub = self.subscripts.get(node.identifier, 0)
        init_str = f" = {node.initializer.accept(self)}" if node.initializer else ""
        return f"{node.type_spec} {node.identifier}_{sub}{init_str}"

    def visit_return_stmt(self, node: ReturnStmt) -> str:
        expr_str = f" {node.expression.accept(self)}" if node.expression else ""
        return f"return{expr_str}"

    def visit_expr_stmt(self, node: ExprStmt) -> str:
        if node.expression:
            return node.expression.accept(self)
        return ""

    def visit_assignment_expr(self, node: AssignmentExpr) -> str:
        return f"{node.target.accept(self)} {node.operator} {node.value.accept(self)}"

    def visit_binary_expr(self, node: BinaryExpr) -> str:
        return f"({node.left.accept(self)} {node.operator} {node.right.accept(self)})"

    def visit_unary_expr(self, node: UnaryExpr) -> str:
        return f"{node.operator}{node.target.accept(self)}"

    def visit_call_expr(self, node: CallExpr) -> str:
        args_str = ", ".join([arg.accept(self) for arg in node.arguments])
        return f"{node.callee.accept(self)}({args_str})"

    def visit_array_access_expr(self, node: ArrayAccessExpr) -> str:
        return f"{node.target.accept(self)}[{node.index.accept(self)}]"

    def visit_member_access_expr(self, node: MemberAccessExpr) -> str:
        return f"{node.target.accept(self)}{node.operator}{node.member}"

    def visit_identifier(self, node: Identifier) -> str:
        sub = self.subscripts.get(node.name, 0)
        return f"{node.name}_{sub}"

    def visit_int_literal(self, node: IntLiteral) -> str:
        return node.raw_value

    def visit_float_literal(self, node: FloatLiteral) -> str:
        return node.raw_value

    def visit_char_literal(self, node: CharLiteral) -> str:
        return node.value

    def visit_string_literal(self, node: StringLiteral) -> str:
        return node.value


class SSATransformer:
    """Transforms a standard CFG into Static Single Assignment (SSA) form (Section 7 - Bonus)."""
    
    def __init__(self, cfg: CFG, dominance_analyzer: DominanceAnalyzer):
        self.cfg = cfg
        self.dom = dominance_analyzer
        
        # Maps variable name -> List of basic blocks that define it
        self.def_sites: Dict[str, Set[BasicBlock]] = {}
        # Maps Block -> Set of variable names requiring a phi-function at its top
        self.phi_placements: Dict[BasicBlock, Set[str]] = {b: set() for b in cfg.blocks}
        # Maps Block -> List of phi-function strings representing LHS & arguments
        # e.g., "x_2 = phi(x_1, x_3)"
        self.phi_functions: Dict[BasicBlock, List[str]] = {b: [] for b in cfg.blocks}
        
        # Renaming state variables
        self.counters: Dict[str, int] = {}
        self.stacks: Dict[str, List[int]] = {}
        self.ssa_blocks: Dict[BasicBlock, List[str]] = {b: [] for b in cfg.blocks}

    def transform(self):
        """Executes Cytron's SSA construction algorithm."""
        # Step 1: Collect all variable definition sites
        self._collect_definitions()
        
        # Step 2: Insert Phi-functions at dominance frontiers of definition sites
        self._place_phi_functions()
        
        # Step 3: Perform variables renaming traversing the Dominator Tree
        self._rename_variables()

    def _collect_definitions(self):
        """Scans CFG blocks to identify all variables and their assignment sites."""
        for block in self.cfg.blocks:
            for stmt in block.statements:
                # Unpack ExprStmt to inspect its inner expression
                inner_stmt = stmt.expression if (isinstance(stmt, ExprStmt) and stmt.expression is not None) else stmt
                
                if isinstance(stmt, VarDecl):
                    var_name = stmt.identifier
                    if var_name not in self.def_sites:
                        self.def_sites[var_name] = set()
                    self.def_sites[var_name].add(block)
                elif isinstance(inner_stmt, AssignmentExpr) and isinstance(inner_stmt.target, Identifier):
                    var_name = inner_stmt.target.name
                    if var_name not in self.def_sites:
                        self.def_sites[var_name] = set()
                    self.def_sites[var_name].add(block)

    def _place_phi_functions(self):
        """Implements Cytron's worklist algorithm to place phi-functions."""
        for var_name, sites in self.def_sites.items():
            worklist = list(sites)
            added_to_phi = set()
            
            while worklist:
                node_x = worklist.pop(0)
                # Query Dominance Frontier (DF) computed in our dominance pass
                for node_y in self.dom.get_dominance_frontier(node_x):
                    if node_y not in added_to_phi:
                        self.phi_placements[node_y].add(var_name)
                        added_to_phi.add(node_y)
                        if node_y not in sites:
                            worklist.append(node_y)

    def _rename_variables(self):
        """Performs renaming via preorder traversal over the Dominator Tree."""
        # Initialize subscripts stacks
        for var in self.def_sites.keys():
            self.counters[var] = 0
            self.stacks[var] = [0]  # Base subscript is 0

        # Construct Dominator Tree adjacency list
        dom_tree = self.dom.get_dominator_tree_structure()

        # Build phi structures inside blocks (allocates spaces for predecessor args)
        phi_data: Dict[BasicBlock, Dict[str, List[Optional[str]]]] = {
            b: {var: [None] * len(b.predecessors) for var in self.phi_placements[b]}
            for b in self.cfg.blocks
        }

        def rename(block: BasicBlock):
            pushed_vars: List[Tuple[str, int]] = []
            phi_lhs: Dict[str, int] = {} # Locally store the correct LHS subscript assigned at the start of block

            # 1. Rename placed Phi functions LHS
            for var in sorted(list(self.phi_placements[block])):
                new_sub = self.counters[var] + 1
                self.counters[var] = new_sub
                self.stacks[var].append(new_sub)
                pushed_vars.append((var, new_sub))
                phi_lhs[var] = new_sub # Save local subscript mapping
                
                # Register LHS of phi
                phi_data[block][var] = [f"{var}_phi_placeholder"] * len(block.predecessors)

            # 2. Rename statement uses and definitions separately to ensure LHS has new sub, RHS has old sub
            for stmt in block.statements:
                # We unpack ExprStmt to inspect its inner expression
                inner_stmt = stmt.expression if (isinstance(stmt, ExprStmt) and stmt.expression is not None) else stmt
                
                if isinstance(stmt, VarDecl):
                    var_name = stmt.identifier
                    # Format initializer with OLD subscripts
                    init_str = ""
                    if stmt.initializer:
                        formatter = SSAFormatter(active_subscripts={v: s[-1] for v, s in self.stacks.items()})
                        init_str = f" = {formatter.format_node(stmt.initializer)}"
                    
                    # Generate and push NEW subscript
                    new_sub = self.counters[var_name] + 1
                    self.counters[var_name] = new_sub
                    self.stacks[var_name].append(new_sub)
                    pushed_vars.append((var_name, new_sub))
                    
                    self.ssa_blocks[block].append(f"{stmt.type_spec} {var_name}_{new_sub}{init_str}")

                elif isinstance(inner_stmt, AssignmentExpr) and isinstance(inner_stmt.target, Identifier):
                    var_name = inner_stmt.target.name
                    # Format RHS value with OLD subscripts
                    formatter = SSAFormatter(active_subscripts={v: s[-1] for v, s in self.stacks.items()})
                    val_str = formatter.format_node(inner_stmt.value)
                    
                    # Generate and push NEW subscript
                    new_sub = self.counters[var_name] + 1
                    self.counters[var_name] = new_sub
                    self.stacks[var_name].append(new_sub)
                    pushed_vars.append((var_name, new_sub))
                    
                    self.ssa_blocks[block].append(f"{var_name}_{new_sub} {inner_stmt.operator} {val_str}")

                else:
                    # Pure read/use statement (IfStmt, WhileStmt, ExprStmt, ReturnStmt)
                    formatter = SSAFormatter(active_subscripts={v: s[-1] for v, s in self.stacks.items()})
                    self.ssa_blocks[block].append(formatter.format_node(stmt))

            # 3. Fill in phi-arguments in CFG successor blocks
            for succ in block.successors:
                if succ in phi_data:
                    # Find which predecessor index 'block' corresponds to
                    pred_idx = succ.predecessors.index(block)
                    for var in phi_data[succ].keys():
                        active_sub = self.stacks[var][-1]
                        phi_data[succ][var][pred_idx] = f"{var}_{active_sub}"

            # 4. Recurse on children in Dominator Tree
            for child in sorted(dom_tree.get(block, []), key=lambda b: b.id):
                rename(child)

            # 5. Pop active subscripts stacks to restore context
            for var, sub in pushed_vars:
                self.stacks[var].pop()

            # 6. Render finalized Phi function strings
            for var in sorted(list(self.phi_placements[block])):
                lhs_sub = phi_lhs[var] # Retrieve the correct local subscript
                args = phi_data[block][var]
                args_str = ", ".join(args)
                self.phi_functions[block].append(f"{var}_{lhs_sub} = phi({args_str})")

        # Start recursive renaming from ENTRY
        rename(self.cfg.entry)