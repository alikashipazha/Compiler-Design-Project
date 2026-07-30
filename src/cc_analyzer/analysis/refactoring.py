import difflib
from typing import List, Optional, Tuple, Set, Dict
from cc_analyzer.core.location import SourceLocation
from cc_analyzer.core.tokens import TokenType, Token
from cc_analyzer.core.lexer import Lexer
from cc_analyzer.core.parser import Parser
from cc_analyzer.semantics.symbol_table import Scope, Symbol
from cc_analyzer.semantics.type_checker import TypeChecker
from cc_analyzer.core.ast_nodes import (
    ASTNode, Program, VarDecl, Param, FunctionDecl, StructDecl, Block,
    IfStmt, WhileStmt, ForStmt, ReturnStmt, ExprStmt, AssignmentExpr,
    BinaryExpr, UnaryExpr, CallExpr, ArrayAccessExpr, MemberAccessExpr,
    Identifier
)

class ReferenceCollector:
    """AST Visitor that collects every scope-aware reference location for a specific Target Symbol (Section 6.3)."""
    
    def __init__(self, target_symbol: Symbol, type_checker: TypeChecker):
        self.target_symbol = target_symbol
        self.type_checker = type_checker
        self.reference_locations: Set[Tuple[int, int]] = set()

    def collect(self, program: Program) -> List[SourceLocation]:
        self.reference_locations.clear()
        
        # The declaration site is naturally a reference (the definition)
        decl_loc = self.target_symbol.definition_loc
        self.reference_locations.add((decl_loc.line, decl_loc.column))
        
        program.accept(self)
        
        # Map back to SourceLocation objects sorted by line and column
        sorted_locs = sorted(list(self.reference_locations))
        return [SourceLocation(line, col) for line, col in sorted_locs]

    def _check_and_add(self, node_name: str, loc: SourceLocation, scope: Scope):
        """Resolves the identifier inside its active scope. If it refers 
        to the target symbol, we collect its location."""
        resolved = scope.lookup(node_name)
        if resolved and resolved.definition_loc == self.target_symbol.definition_loc:
            self.reference_locations.add((loc.line, loc.column))

    # --- Visitor Traversal paths ---

    def visit_program(self, node: Program):
        for decl in node.declarations:
            decl.accept(self)

    def visit_var_decl(self, node: VarDecl):
        # Retrieve the logged scope of this declaration site
        scope = self.type_checker.location_scopes.get((node.location.line, node.location.column))
        if scope:
            self._check_and_add(node.identifier, node.location, scope)
        if node.initializer:
            node.initializer.accept(self)

    def visit_param(self, node: Param):
        pass

    def visit_function_decl(self, node: FunctionDecl):
        scope = self.type_checker.location_scopes.get((node.location.line, node.location.column))
        if scope:
            self._check_and_add(node.identifier, node.location, scope)
            
        for param in node.params:
            p_scope = self.type_checker.location_scopes.get((param.location.line, param.location.column))
            if p_scope:
                self._check_and_add(param.identifier, param.location, p_scope)
                
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
        node.callee.accept(self)
        for arg in node.arguments:
            arg.accept(self)

    def visit_array_access_expr(self, node: ArrayAccessExpr):
        node.target.accept(self)
        node.index.accept(self)

    def visit_member_access_expr(self, node: MemberAccessExpr):
        node.target.accept(self)

    def visit_identifier(self, node: Identifier):
        scope = self.type_checker.location_scopes.get((node.location.line, node.location.column))
        if scope:
            self._check_and_add(node.name, node.location, scope)

    def visit_int_literal(self, node): pass
    def visit_float_literal(self, node): pass
    def visit_char_literal(self, node): pass
    def visit_string_literal(self, node): pass


class RefactoringEngine:
    """Engine providing Go-to-Definition, Find-All-References, Hover documentation, 
    and Scope-aware Safe Rename Refactoring (Section 6.3 & 6.4)."""
    
    def __init__(self, source_code: str):
        self.source = source_code
        self.tokens: List[Token] = []
        self.parser_errors: List[str] = []
        self.ast_program: Optional[Program] = None
        self.type_checker = TypeChecker()
        self._analyze()

    def _analyze(self):
        # Lex and parse to obtain AST and populated hierarchical scopes
        lexer = Lexer(self.source)
        self.tokens = lexer.tokenize(keep_comments=False)
        
        parser = Parser(self.tokens)
        self.ast_program = parser.parse()
        self.parser_errors = parser.errors
        
        if self.ast_program:
            self.type_checker.check(self.ast_program)

    def _get_active_scope(self, line: int, column: int) -> Scope:
        active_scope = self.type_checker.global_scope
        best_loc = (0, 0)
        for loc, scope in self.type_checker.location_scopes.items():
            if loc[0] < line or (loc[0] == line and loc[1] <= column):
                if loc > best_loc:
                    best_loc = loc
                    active_scope = scope
        return active_scope

    def _get_symbol_at(self, line: int, column: int) -> Optional[Tuple[Symbol, Scope]]:
        """Locates the identifier token at the cursor coordinates and resolves its Symbol and Scope."""
        for token in self.tokens:
            if token.type == TokenType.IDENT and token.location.line == line:
                if token.location.column <= column <= (token.location.column + len(token.lexeme)):
                    active_scope = self._get_active_scope(line, column)
                    sym = active_scope.lookup(token.lexeme)
                    if sym:
                        return sym, active_scope
        return None

    def goto_definition(self, line: int, column: int) -> Optional[dict]:
        """Returns the exact declaration site of the symbol under the cursor (Section 6.3)."""
        res = self._get_symbol_at(line, column)
        if res:
            sym, _ = res
            return {
                "symbol": sym.name,
                "kind": sym.kind,
                "type": sym.type,
                "defined_at": {
                    "line": sym.definition_loc.line,
                    "column": sym.definition_loc.column
                }
            }
        return None

    def find_all_references(self, line: int, column: int) -> Optional[List[dict]]:
        """Returns every scope-aware usage location (reads and writes) of the symbol (Section 6.3)."""
        res = self._get_symbol_at(line, column)
        if res and self.ast_program:
            sym, _ = res
            collector = ReferenceCollector(sym, self.type_checker)
            ref_locations = collector.collect(self.ast_program)
            
            return [{
                "line": loc.line,
                "column": loc.column
            } for loc in ref_locations]
        return None

    def hover(self, line: int, column: int) -> Optional[dict]:
        """Returns full type signature and any attached preceding Javadoc/Doxygen documentation (Section 6.3)."""
        res = self._get_symbol_at(line, column)
        if res:
            sym, _ = res
            
            # Find attached documentation comment
            # We tokenize the source KEEPING comments, then search backwards from the symbol declaration
            doc_comment = ""
            lexer_with_comments = Lexer(self.source)
            all_tokens = lexer_with_comments.tokenize(keep_comments=True)
            
            # Find the index of the declaration token
            decl_idx = -1
            for idx, t in enumerate(all_tokens):
                if t.location == sym.definition_loc and t.lexeme == sym.name:
                    decl_idx = idx
                    break
                    
            if decl_idx != -1:
                # Scan backwards from the declaration token (or its type keyword preceding it)
                # To find the immediately preceding comment token
                search_idx = decl_idx - 1
                while search_idx >= 0:
                    prev_t = all_tokens[search_idx]
                    if prev_t.type in (TokenType.COMMENT_SINGLE, TokenType.COMMENT_BLOCK):
                        doc_comment = prev_t.lexeme
                        break
                    elif prev_t.lexeme in ("struct", "int", "float", "char", "void", "double", "*", " ", "\t", "\n", "\r"):
                        # Skip types and formatting tokens to reach the block doc
                        search_idx -= 1
                    else:
                        break

            detail = f"{sym.type} {sym.name}"
            if sym.kind == "function" and sym.signature:
                params, ret = sym.signature
                detail = f"{ret} {sym.name}({', '.join(params)})"

            return {
                "name": sym.name,
                "kind": sym.kind,
                "detail": detail,
                "documentation": doc_comment.strip()
            }
        return None

    def rename(self, line: int, column: int, new_name: str) -> Optional[str]:
        """Performs a safe, scope-aware rename operation and returns a unified diff (Section 6.4)."""
        res = self._get_symbol_at(line, column)
        if not res or not self.ast_program:
            return None
            
        sym, scope = res
        
        # 1. Conflict Check: check if the new name already exists locally in the target scope
        if scope.lookup_local(new_name) is not None:
            raise ValueError(f"Conflict Error: Symbol '{new_name}' already defined in the target scope.")

        # 2. Shadow Check (Semantics Preservation): 
        # Check if renaming sym to new_name causes accidental capture or shadowing
        outer_shadow = scope.lookup(new_name)
        if outer_shadow is not None:
            # Re-binding with outer name triggers warning/error
            raise ValueError(f"Shadow Conflict: Renaming would shadow outer definition of '{new_name}' at {outer_shadow.definition_loc}.")

        # 3. Collect all scope-aware reference locations
        collector = ReferenceCollector(sym, self.type_checker)
        ref_locations = collector.collect(self.ast_program)

        # 4. Generate modified source code and create Unified Diff
        orig_lines = self.source.splitlines(keepends=True)
        mod_lines = orig_lines.copy()

        # To replace names on lines correctly, group ref locations by line index (0-based)
        # We perform replacements in reverse column order to preserve preceding column offsets!
        refs_by_line: Dict[int, List[SourceLocation]] = {}
        for loc in ref_locations:
            line_idx = loc.line - 1
            if line_idx not in refs_by_line:
                refs_by_line[line_idx] = []
            refs_by_line[line_idx].append(loc)

        for line_idx, locs in refs_by_line.items():
            # Sort locations by column in reverse
            sorted_locs = sorted(locs, key=lambda l: l.column, reverse=True)
            line_str = orig_lines[line_idx]
            
            for loc in sorted_locs:
                col_idx = loc.column - 1
                # Replace the exact lexeme occurrence
                before = line_str[:col_idx]
                after = line_str[col_idx + len(sym.name):]
                line_str = before + new_name + after
                
            mod_lines[line_idx] = line_str

        # Generate unified diff representation
        diff = difflib.unified_diff(
            orig_lines, 
            mod_lines, 
            fromfile="main.c (Before)", 
            tofile="main.c (After)", 
            n=2
        )
        return "".join(diff)

    def get_diagnostics(self) -> List[dict]:
        """Aggregate all Lexer, Parser, and Semantic diagnostics within RefactoringEngine."""
        all_diags = []
        
        # 1. Lexer errors
        for token in self.tokens:
            if token.type == TokenType.INVALID:
                msg = f"Lexical error: invalid token '{token.lexeme}'"
                if token.lexeme.startswith('"'):
                    msg = "Unterminated string literal"
                elif token.lexeme.startswith("/*"):
                    msg = "Unterminated block comment"
                all_diags.append({
                    "severity": "Error",
                    "message": msg,
                    "file": "main.c",
                    "line": token.location.line,
                    "column": token.location.column,
                    "length": len(token.lexeme)
                })

        # 2. Parser errors
        for err in self.parser_errors:
            all_diags.append({
                "severity": "Error",
                "message": err,
                "file": "main.c",
                "line": 1,
                "column": 1,
                "length": 1
            })

        # 3. Semantic errors
        all_diags.extend(self.type_checker.diagnostics)
        
        return all_diags