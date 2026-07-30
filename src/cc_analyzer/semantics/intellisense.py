from typing import List, Optional, Tuple, Set, Dict
from cc_analyzer.core.location import SourceLocation
from cc_analyzer.core.tokens import TokenType, Token
from cc_analyzer.core.lexer import Lexer
from cc_analyzer.core.parser import Parser
from cc_analyzer.semantics.symbol_table import Scope, Symbol
from cc_analyzer.semantics.type_checker import TypeChecker
from cc_analyzer.core.ast_nodes import Program

class IntellisenseEngine:
    """Context-aware auto-completion, hover info, and aggregated diagnostic compiler engine (Section 5.4 & 5.5)."""
    
    C_KEYWORDS = ["if", "else", "while", "for", "return", "struct", "int", "float", "char", "void", "double"]

    def __init__(self, source_code: str):
        self.source = source_code
        self.tokens: List[Token] = []
        self.parser_errors: List[str] = []
        self.ast_program: Optional[Program] = None
        self.type_checker = TypeChecker()
        
        # Build the compiler front-end pipeline & analyze semantics
        self._analyze()

    def _analyze(self):
        lexer = Lexer(self.source)
        self.tokens = lexer.tokenize(keep_comments=False)
        
        parser = Parser(self.tokens)
        self.ast_program = parser.parse()
        self.parser_errors = parser.errors
        
        # Perform semantic & type check pass
        if self.ast_program:
            self.type_checker.check(self.ast_program)

    def get_diagnostics(self) -> List[dict]:
        """Aggregate all Lexer, Parser, and Semantic diagnostics (Section 5.5)."""
        all_diags = []
        
        # 1. Lexer errors (INVALID tokens)
        for token in self.tokens:
            if token.type == TokenType.INVALID:
                # Determine lexical error context
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
            # We standardize parser errors as raw structured errors
            all_diags.append({
                "severity": "Error",
                "message": err,
                "file": "main.c",
                "line": 1,
                "column": 1,
                "length": 1
            })

        # 3. Semantic & type errors
        all_diags.extend(self.type_checker.diagnostics)
        
        return all_diags

    def _get_active_scope(self, line: int, column: int) -> Scope:
        """Finds the innermost scope active at or before the given line and column."""
        active_scope = self.type_checker.global_scope
        best_loc = (0, 0)
        
        # Walk logged scope locations to locate the closest active scope at the cursor
        for loc, scope in self.type_checker.location_scopes.items():
            if loc[0] < line or (loc[0] == line and loc[1] <= column):
                if loc > best_loc:
                    best_loc = loc
                    active_scope = scope
        return active_scope

    def get_hover_info(self, line: int, column: int) -> Optional[dict]:
        """Returns structured hover information for a symbol at a cursor location (Section 5.4)."""
        # Find if there is an identifier token matching the cursor exactly
        for token in self.tokens:
            if token.type == TokenType.IDENT and token.location.line == line:
                # Check if cursor is over the token span
                if token.location.column <= column <= (token.location.column + len(token.lexeme)):
                    active_scope = self._get_active_scope(line, column)
                    sym = active_scope.lookup(token.lexeme)
                    if sym:
                        detail = f"{sym.type} {sym.name}"
                        if sym.kind == "function" and sym.signature:
                            param_types, ret = sym.signature
                            detail = f"{ret} {sym.name}({', '.join(param_types)})"
                        return {
                            "name": sym.name,
                            "kind": sym.kind,
                            "detail": detail,
                            "definition_loc": str(sym.definition_loc)
                        }
        return None

    def get_completions(self, line: int, column: int) -> List[dict]:
        """Returns context-aware autocompletions at the cursor (Section 5.4)."""
        # Find the token immediately preceding the cursor on the same line
        prec_token = None
        for t in self.tokens:
            if t.location.line == line and t.location.column < column:
                if prec_token is None or t.location.column > prec_token.location.column:
                    prec_token = t

        completions = []
        
        # 1. Member Access completion after '.' or '->'
        if prec_token and prec_token.type in (TokenType.OP_DOT, TokenType.OP_ARROW):
            # Find the identifier preceding the operator (LHS)
            lhs_token = None
            for t in self.tokens:
                if t.location.line == line and t.location.column < prec_token.location.column:
                    if lhs_token is None or t.location.column > lhs_token.location.column:
                        lhs_token = t
                        
            if lhs_token and lhs_token.type == TokenType.IDENT:
                active_scope = self._get_active_scope(line, column)
                lhs_sym = active_scope.lookup(lhs_token.lexeme)
                if lhs_sym:
                    target_type = lhs_sym.type
                    struct_name = None
                    if prec_token.type == TokenType.OP_DOT and target_type.startswith("struct "):
                        struct_name = target_type.split(" ")[1]
                    elif prec_token.type == TokenType.OP_ARROW and target_type.startswith("struct "):
                        struct_name = target_type.split(" ")[1].replace("*", "")
                        
                    if struct_name in self.type_checker.struct_scopes:
                        # Suggest fields from member scope
                        member_scope = self.type_checker.struct_scopes[struct_name]
                        for field in member_scope.symbols.values():
                            completions.append({
                                "label": field.name,
                                "kind": "Field",
                                "detail": field.type,
                                "sortOrder": 1
                            })
            return completions

        # 2. General Scope Completion
        active_scope = self._get_active_scope(line, column)
        scope = active_scope
        visited_names = set()
        
        # Collect visible symbols walking up the scope tree
        while scope is not None:
            for sym in scope.symbols.values():
                if sym.name not in visited_names and not sym.name.startswith("struct "):
                    visited_names.add(sym.name)
                    completions.append({
                        "label": sym.name,
                        "kind": "Method" if sym.kind == "function" else "Variable",
                        "detail": sym.type if sym.kind != "function" else f"{sym.signature[1]} function",
                        "sortOrder": 2
                    })
            scope = scope.parent

        # Suggest keywords
        for kw in self.C_KEYWORDS:
            if kw not in visited_names:
                completions.append({
                    "label": kw,
                    "kind": "Keyword",
                    "detail": "C keyword",
                    "sortOrder": 3
                })
                
        return completions