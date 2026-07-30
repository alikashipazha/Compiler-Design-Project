from typing import Dict, List, Optional, Set, Tuple
from cc_analyzer.core.location import SourceLocation
from cc_analyzer.core.tokens import TokenType, Token
from cc_analyzer.semantics.symbol_table import Scope, Symbol
from cc_analyzer.core.ast_nodes import (
    ASTNode, Program, VarDecl, Param, FunctionDecl, StructDecl, Block,
    IfStmt, WhileStmt, ForStmt, ReturnStmt, ExprStmt, AssignmentExpr,
    BinaryExpr, UnaryExpr, CallExpr, ArrayAccessExpr, MemberAccessExpr,
    Identifier, IntLiteral, FloatLiteral, CharLiteral, StringLiteral
)

class TypeChecker:
    """AST Visitor that implements semantic analysis, scope resolution, and C-style type checking (Section 5.3)."""
    
    def __init__(self):
        self.global_scope = Scope("global")
        self.current_scope = self.global_scope
        self.struct_scopes: Dict[str, Scope] = {} # Custom struct name -> member scope mapping
        self.diagnostics: List[dict] = []
        self.current_function: Optional[Symbol] = None
        # Maps (line, column) -> Scope active at that identifier (Required for Intellisense lookup)
        self.location_scopes: Dict[Tuple[int, int], Scope] = {}

    def check(self, program: Program) -> List[dict]:
        """Runs the semantic analyzer on the AST and returns a list of collected diagnostics."""
        self.diagnostics.clear()
        self.location_scopes.clear()
        
        # Pass 1: Collect top-level declarations (Section 5.1.2)
        self._collect_declarations(program)
        
        # Pass 2: Lexical Scope Resolution & Type Verification
        program.accept(self)
        
        return self.diagnostics

    def _report(self, severity: str, message: str, loc: SourceLocation, length: int = 1):
        """Helper to append a structured, machine-readable diagnostic (Section 5.5)."""
        self.diagnostics.append({
            "severity": severity,
            "message": message,
            "file": "main.c",
            "line": loc.line,
            "column": loc.column,
            "length": length
        })

    # --- Helper C Type Methods ---

    def _is_numeric(self, type_str: str) -> bool:
        return type_str in ("int", "float", "double", "char")

    def _is_pointer(self, type_str: str) -> bool:
        return type_str.endswith("*")

    def _dereference_type(self, type_str: str) -> Optional[str]:
        if self._is_pointer(type_str):
            return type_str[:-1] # Remove one '*'
        return None

    def _address_of_type(self, type_str: str) -> str:
        return type_str + "*"

    def _check_assignability(self, left_type: str, right_type: str, loc: SourceLocation, lexeme_len: int):
        """Verifies if a right-hand type can be implicitly assigned to a left-hand type in C."""
        if left_type == right_type:
            return

        # Implicit numeric promotions
        if self._is_numeric(left_type) and self._is_numeric(right_type):
            if left_type == "int" and (right_type == "double" or right_type == "float"):
                # Section 5.3.1 - Warning for float -> int loses precision
                self._report("Warning", f"double to int conversion loses precision", loc, lexeme_len)
            return

        # Incompatible pointer assignments
        if self._is_pointer(left_type) and self._is_pointer(right_type):
            self._report("Warning", f"Assignment from incompatible pointer type '{right_type}' to '{left_type}'", loc, lexeme_len)
            return

        # Assigning numeric directly to pointer (e.g. char* s = 42)
        if self._is_pointer(left_type) and right_type == "int":
            self._report("Error", f"Cannot implicitly assign 'int' to pointer type '{left_type}'", loc, lexeme_len)
            return

        # Catch-all incompatibilities
        self._report("Error", f"Incompatible types in assignment: cannot assign '{right_type}' to '{left_type}'", loc, lexeme_len)

    # --- Pass 1: Declaration Scanner ---

    def _collect_declarations(self, program: Program):
        for decl in program.declarations:
            if isinstance(decl, StructDecl):
                # Save struct type and instantiate its dedicated member scope
                if decl.identifier in self.struct_scopes:
                    self._report("Error", f"Duplicate struct declaration: '{decl.identifier}'", decl.location, len(decl.identifier))
                    continue
                
                member_scope = Scope(f"struct_{decl.identifier}", is_struct_scope=True)
                self.struct_scopes[decl.identifier] = member_scope
                
                # Register struct globally as a valid type
                struct_type_name = f"struct {decl.identifier}"
                struct_symbol = Symbol(struct_type_name, "type", struct_type_name, decl.location)
                self.global_scope.define(struct_symbol)
                
                # Fill struct member scopes
                for member in decl.members:
                    mem_sym = Symbol(member.identifier, "struct_member", member.type_spec, member.location)
                    mem_sym.is_initialized = True  # Struct members don't require linear init check
                    if not member_scope.define(mem_sym):
                        self._report("Error", f"Duplicate member declaration: '{member.identifier}'", member.location, len(member.identifier))

            elif isinstance(decl, FunctionDecl):
                # Save function signatures
                param_types = [p.type_spec for p in decl.params]
                sig = (param_types, decl.type_spec)
                
                func_sym = Symbol(decl.identifier, "function", decl.type_spec, decl.location, signature=sig)
                func_sym.is_initialized = True
                
                if not self.global_scope.define(func_sym):
                    self._report("Error", f"Duplicate function declaration: '{decl.identifier}'", decl.location, len(decl.identifier))

    # --- Pass 2: Main Semantic Traversal ---

    def visit_program(self, node: Program):
        for decl in node.declarations:
            decl.accept(self)

    def visit_var_decl(self, node: VarDecl):
        # Register active scope for Intellisense lookup
        self.location_scopes[(node.location.line, node.location.column)] = self.current_scope

        # 1. Verify type specifier exists
        is_struct_type = node.type_spec.startswith("struct ")
        if is_struct_type:
            struct_name = node.type_spec.split(" ")[1].replace("*", "")
            if struct_name not in self.struct_scopes:
                self._report("Error", f"Undefined struct type: '{node.type_spec}'", node.location, len(node.type_spec))
                return

        # 2. Check duplicate declarations in current block scope
        if self.current_scope.lookup_local(node.identifier) is not None:
            self._report("Error", f"Duplicate declaration of symbol '{node.identifier}' in this scope", node.location, len(node.identifier))
            return

        # 3. Check for shadowing warning (Section 5.2 rule 5)
        outer_shadow = self.current_scope.lookup(node.identifier)
        if outer_shadow is not None:
            self._report("Warning", f"Variable '{node.identifier}' shadows an outer declaration at {outer_shadow.definition_loc}", node.location, len(node.identifier))

        # 4. Create symbol entry
        symbol = Symbol(node.identifier, "variable", node.type_spec, node.location)
        
        # 5. Handle initializers and verify compatibility
        if node.initializer:
            init_type = node.initializer.accept(self)
            if init_type is not None:
                self._check_assignability(node.type_spec, init_type, node.location, len(node.identifier))
            symbol.is_initialized = True
            
        self.current_scope.define(symbol)

    def visit_param(self, node: Param):
        # Parameters are visited inside FunctionDecl logic, so we pass
        pass

    def visit_function_decl(self, node: FunctionDecl):
        # Register active scope for Intellisense
        self.location_scopes[(node.location.line, node.location.column)] = self.global_scope

        # Find registered function symbol
        func_sym = self.global_scope.lookup_local(node.identifier)
        self.current_function = func_sym
        
        # Create dedicated block scope for the function body containing all its params
        func_body_scope = Scope(f"{node.identifier}_body", parent=self.global_scope)
        self.current_scope = func_body_scope
        
        # Register parameters inside the function scope
        for param in node.params:
            if func_body_scope.lookup_local(param.identifier) is not None:
                self._report("Error", f"Duplicate parameter name: '{param.identifier}'", param.location, len(param.identifier))
                continue
                
            p_sym = Symbol(param.identifier, "parameter", param.type_spec, param.location)
            p_sym.is_initialized = True # Params are naturally initialized
            func_body_scope.define(p_sym)
            self.location_scopes[(param.location.line, param.location.column)] = func_body_scope

        # Traverse body block statements
        node.block.accept(self)
        
        # At end of function, collect 'unused variable' info-diagnostics (Section 5.5 rules)
        for sym in func_body_scope.symbols.values():
            if not sym.is_used and sym.kind == "variable":
                self._report("Info", f"Variable '{sym.name}' is declared but never read", sym.definition_loc, len(sym.name))

        # Reset scope back to global
        self.current_scope = self.global_scope
        self.current_function = None

    def visit_struct_decl(self, node: StructDecl):
        # Struct definitions were fully scanned and populated in Pass 1, so we skip
        pass

    def visit_block(self, node: Block):
        # Blocks (enclosed in {}) instantiate nested child scopes
        block_scope = Scope("block", parent=self.current_scope)
        self.current_scope = block_scope
        
        for stmt in node.statements:
            stmt.accept(self)
            
        # Warn for unused local block variables
        for sym in block_scope.symbols.values():
            if not sym.is_used and sym.kind == "variable":
                self._report("Info", f"Variable '{sym.name}' is declared but never read", sym.definition_loc, len(sym.name))
                
        self.current_scope = self.current_scope.parent

    def visit_if_stmt(self, node: IfStmt):
        cond_type = node.condition.accept(self)
        if cond_type and not self._is_numeric(cond_type) and not self._is_pointer(cond_type):
            self._report("Error", f"Condition inside if statement must evaluate to a numeric or pointer type", node.condition.location)
            
        node.then_branch.accept(self)
        if node.else_branch:
            node.else_branch.accept(self)

    def visit_while_stmt(self, node: WhileStmt):
        cond_type = node.condition.accept(self)
        if cond_type and not self._is_numeric(cond_type) and not self._is_pointer(cond_type):
            self._report("Error", f"Condition inside while statement must evaluate to a numeric or pointer type", node.condition.location)
            
        node.body.accept(self)

    def visit_for_stmt(self, node: ForStmt):
        if node.init:
            node.init.accept(self)
        if node.condition:
            cond_type = node.condition.accept(self)
            if cond_type and not self._is_numeric(cond_type) and not self._is_pointer(cond_type):
                self._report("Error", f"For condition must evaluate to a numeric or pointer type", node.condition.location)
        if node.increment:
            node.increment.accept(self)
            
        node.body.accept(self)

    def visit_return_stmt(self, node: ReturnStmt):
        expr_type = "void"
        if node.expression:
            expr_type = node.expression.accept(self)
            
        if self.current_function:
            ret_type = self.current_function.type
            if expr_type == "void" and ret_type != "void":
                self._report("Error", f"Void return inside function returning '{ret_type}'", node.location)
            elif expr_type != "void" and ret_type == "void":
                self._report("Error", f"Value return inside void function", node.location)
            elif expr_type != "void":
                # Check compatibility of returned type
                self._check_assignability(ret_type, expr_type, node.location, 6) # 'return' length is 6

    def visit_expr_stmt(self, node: ExprStmt):
        if node.expression:
            node.expression.accept(self)

    # --- Expressions Evaluation (Returns computed string types) ---

    def visit_assignment_expr(self, node: AssignmentExpr):
        left_type = node.target.accept(self)
        right_type = node.value.accept(self)
        
        if left_type and right_type:
            # Check lvalue constraints and assignability
            self._check_assignability(left_type, right_type, node.location, 1)
            
            # Linear init tracker: Mark left target identifier as initialized
            if isinstance(node.target, Identifier):
                sym = self.current_scope.lookup(node.target.name)
                if sym:
                    sym.is_initialized = True
                    
        node.type_annotation = left_type
        return left_type

    def visit_binary_expr(self, node: BinaryExpr):
        left_type = node.left.accept(self)
        right_type = node.right.accept(self)
        
        if not left_type or not right_type:
            return None

        # Pointer comparison operations in C
        if node.operator in ("==", "!=", "<", ">", "<=", ">="):
            if self._is_pointer(left_type) or self._is_pointer(right_type):
                node.type_annotation = "int"
                return "int"

        # Math promotions
        if self._is_numeric(left_type) and self._is_numeric(right_type):
            if left_type == "double" or right_type == "double":
                computed = "double"
            elif left_type == "float" or right_type == "float":
                computed = "float"
            else:
                computed = "int"
                
            # Relational operators always yield bool representations (int in C)
            if node.operator in ("==", "!=", "<", ">", "<=", ">=", "&&", "||"):
                computed = "int"
                
            node.type_annotation = computed
            return computed

        self._report("Error", f"Invalid operands to binary expression: '{left_type}' and '{right_type}'", node.location)
        return None

    def visit_unary_expr(self, node: UnaryExpr):
        target_type = node.target.accept(self)
        if not target_type:
            return None

        if node.operator == "-":
            if not self._is_numeric(target_type):
                self._report("Error", f"Operand of '-' must be numeric (got '{target_type}')", node.location)
                return None
            node.type_annotation = target_type
            return target_type

        elif node.operator == "!":
            if not self._is_numeric(target_type) and not self._is_pointer(target_type):
                self._report("Error", f"Operand of '!' must be numeric or pointer", node.location)
                return None
            node.type_annotation = "int"
            return "int"

        elif node.operator == "&":
            # Address-of: T -> T*
            res_type = self._address_of_type(target_type)
            node.type_annotation = res_type
            return res_type

        elif node.operator == "*":
            # Dereference pointer: T* -> T
            res_type = self._dereference_type(target_type)
            if not res_type:
                self._report("Error", f"Cannot dereference non-pointer type '{target_type}'", node.location)
                return None
            node.type_annotation = res_type
            return res_type

        return None

    def visit_call_expr(self, node: CallExpr):
        # Look up function symbol
        if not isinstance(node.callee, Identifier):
            self._report("Error", "Callee must be a function identifier", node.location)
            return None

        func_sym = self.current_scope.lookup(node.callee.name)
        if not func_sym or func_sym.kind != "function":
            self._report("Error", f"Undefined function: '{node.callee.name}'", node.location, len(node.callee.name))
            return None

        # Verify argument count and compatibility against signature (Section 5.3.1 rules)
        arg_types, ret_type = func_sym.signature
        if len(node.arguments) != len(arg_types):
            self._report("Error", f"Function '{node.callee.name}' expected {len(arg_types)} arguments (got {len(node.arguments)})", node.location, len(node.callee.name))
            return ret_type

        for i, arg in enumerate(node.arguments):
            given_type = arg.accept(self)
            expected_type = arg_types[i]
            if given_type and expected_type:
                self._check_assignability(expected_type, given_type, arg.location, len(node.callee.name))

        node.type_annotation = ret_type
        return ret_type

    def visit_array_access_expr(self, node: ArrayAccessExpr):
        target_type = node.target.accept(self)
        index_type = node.index.accept(self)
        
        if not target_type or not index_type:
            return None

        # Target must be pointer
        if not self._is_pointer(target_type):
            self._report("Error", f"Subscripted value is neither array nor pointer (got '{target_type}')", node.location)
            return None

        # Subscript index must be int
        if index_type != "int":
            self._report("Error", f"Array subscript index must be an integer (got '{index_type}')", node.index.location)

        res_type = self._dereference_type(target_type)
        node.type_annotation = res_type
        return res_type

    def visit_member_access_expr(self, node: MemberAccessExpr):
        target_type = node.target.accept(self)
        if not target_type:
            return None

        struct_name = None
        # Handle dot (.) access
        if node.operator == ".":
            if not target_type.startswith("struct ") or self._is_pointer(target_type):
                self._report("Error", f"Expected struct type before '.' (got '{target_type}')", node.location)
                return None
            struct_name = target_type.split(" ")[1]

        # Handle arrow (->) access
        elif node.operator == "->":
            if not self._is_pointer(target_type) or not target_type.startswith("struct "):
                self._report("Error", f"Expected struct pointer before '->' (got '{target_type}')", node.location)
                return None
            # Extract struct name from 'struct Node*' -> 'Node'
            struct_name = target_type.split(" ")[1].replace("*", "")

        if struct_name not in self.struct_scopes:
            self._report("Error", f"Incomplete or undefined struct definition: '{struct_name}'", node.location)
            return None

        # Look up member in the struct members scope
        member_scope = self.struct_scopes[struct_name]
        member_sym = member_scope.lookup_local(node.member)
        if not member_sym:
            self._report("Error", f"Struct '{struct_name}' has no member named '{node.member}'", node.location, len(node.member))
            return None

        node.type_annotation = member_sym.type
        return member_sym.type

    def visit_identifier(self, node: Identifier):
        # Register active scope for Intellisense
        self.location_scopes[(node.location.line, node.location.column)] = self.current_scope

        # Resolve symbol name from inner to outer scopes (Section 5.2)
        symbol = self.current_scope.lookup(node.name)
        if not symbol:
            self._report("Error", f"Undefined symbol: '{node.name}'", node.location, len(node.name))
            return None

        # linear initialization check: read before write warning
        if symbol.kind in ("variable", "parameter") and not symbol.is_initialized:
            self._report("Warning", f"Variable '{node.name}' may be used uninitialized", node.location, len(node.name))

        # Mark read tracking
        symbol.is_used = True
        node.type_annotation = symbol.type
        return symbol.type

    def visit_int_literal(self, node: IntLiteral):
        node.type_annotation = "int"
        return "int"

    def visit_float_literal(self, node: FloatLiteral):
        node.type_annotation = "double"
        return "double"

    def visit_char_literal(self, node: CharLiteral):
        node.type_annotation = "char"
        return "char"

    def visit_string_literal(self, node: StringLiteral):
        node.type_annotation = "char*"
        return "char*"