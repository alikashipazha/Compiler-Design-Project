from typing import Dict, Tuple, Set, List
from cc_analyzer.core.location import SourceLocation
from cc_analyzer.core.tokens import TokenType, Token
from cc_analyzer.core.lexer import Lexer
from cc_analyzer.core.parser import Parser
from cc_analyzer.core.ast_nodes import (
    ASTNode, Program, VarDecl, Param, FunctionDecl, StructDecl, Block,
    IfStmt, WhileStmt, ForStmt, ReturnStmt, ExprStmt, AssignmentExpr,
    BinaryExpr, UnaryExpr, CallExpr, ArrayAccessExpr, MemberAccessExpr,
    Identifier, IntLiteral, FloatLiteral, CharLiteral, StringLiteral
)

class HighlightAnnotator:
    """AST Visitor that traverses the tree and annotates tokens with context-aware semantic categories."""
    def __init__(self):
        # Maps (line, column) -> Category string
        self.annotations: Dict[Tuple[int, int], str] = {}

    def annotate(self, node: ASTNode):
        node.accept(self)

    def visit_program(self, node: Program):
        for decl in node.declarations:
            decl.accept(self)

    def visit_var_decl(self, node: VarDecl):
        if node.initializer:
            node.initializer.accept(self)

    def visit_param(self, node: Param):
        pass

    def visit_function_decl(self, node: FunctionDecl):
        # Annotate function name
        self.annotations[(node.location.line, node.location.column)] = "FUNCTION_NAME"
        for param in node.params:
            param.accept(self)
        node.block.accept(self)

    def visit_struct_decl(self, node: StructDecl):
        # Annotate struct type name
        self.annotations[(node.location.line, node.location.column)] = "TYPE_NAME"
        for member in node.members:
            member.accept(self)

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
            # Annotate callee as FUNCTION_NAME
            self.annotations[(node.callee.location.line, node.callee.location.column)] = "FUNCTION_NAME"
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


class SyntaxHighlighter:
    """AST-guided Syntax Highlighter generating ANSI Terminal codes and standalone HTML files."""
    
    # ANSI Color mapping (Section 4.4 Rules)
    ANSI_COLORS = {
        "KEYWORD": "\033[1;34m",     # Bold Blue
        "TYPE": "\033[36m",          # Teal/Cyan
        "IDENT": "\033[37m",         # White (default)
        "FUNC": "\033[1;33m",        # Bold Yellow/Gold
        "STRUCT": "\033[1;32m",      # Bold Bright Green
        "LITERAL_NUM": "\033[33m",   # Orange
        "LITERAL_STR": "\033[32m",   # Warm Green
        "OPERATOR": "\033[37m",      # Light Gray
        "COMMENT": "\033[3;90m",     # Dim Gray, Italic
        "INVALID": "\033[4;31m",     # Red Underline
        "RESET": "\033[0m"
    }

    # HTML Class mapping for stylesheet (Section 4.5 Rules)
    HTML_CLASSES = {
        "KEYWORD": "kw",
        "TYPE": "type",
        "IDENT": "id",
        "FUNC": "func",
        "STRUCT": "struct",
        "LITERAL_NUM": "num",
        "LITERAL_STR": "str",
        "OPERATOR": "op",
        "COMMENT": "com",
        "INVALID": "err"
    }

    def __init__(self, source_code: str):
        self.source = source_code
        
        # 1. Lex and parse to gather AST and custom struct names
        lexer_for_parser = Lexer(source_code)
        tokens_for_parser = lexer_for_parser.tokenize(keep_comments=False)
        parser = Parser(tokens_for_parser)
        self.ast = parser.parse()
        self.struct_names = parser.struct_names

        # Annotate context-sensitive identifiers (Function calls, custom struct usages)
        annotator = HighlightAnnotator()
        annotator.annotate(self.ast)
        self.annotations = annotator.annotations

        # 2. Tokenize again, keeping comment tokens to highlight them
        lexer_for_highlight = Lexer(source_code)
        self.tokens = lexer_for_highlight.tokenize(keep_comments=True)

    def _get_category(self, token: Token) -> str:
        """Categorize a token based on its intrinsic type and contextual AST annotations."""
        if token.type == TokenType.INVALID:
            return "INVALID"
        if token.type in (TokenType.COMMENT_SINGLE, TokenType.COMMENT_BLOCK):
            return "COMMENT"
        if token.type in (TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_CHAR, TokenType.KW_VOID, TokenType.KW_DOUBLE):
            return "TYPE"
        if token.type.name.startswith("KW_"):
            return "KEYWORD"
        if token.type in (TokenType.LIT_INT, TokenType.LIT_FLOAT):
            return "LITERAL_NUM"
        if token.type in (TokenType.LIT_STRING, TokenType.LIT_CHAR):
            return "LITERAL_STR"
        if token.type.name.startswith("OP_") or token.type in (
            TokenType.LBRACE, TokenType.RBRACE, TokenType.LPAREN, TokenType.RPAREN,
            TokenType.LBRACK, TokenType.RBRACK, TokenType.SEMICOLON, TokenType.COMMA
        ):
            return "OPERATOR"
            
        if token.type == TokenType.IDENT:
            # Custom declared struct type
            if token.lexeme in self.struct_names:
                return "STRUCT"
            # Semantically annotated identifier (e.g. Function call vs standard variable)
            loc_key = (token.location.line, token.location.column)
            if loc_key in self.annotations:
                ann = self.annotations[loc_key]
                if ann == "FUNCTION_NAME":
                    return "FUNC"
                elif ann == "TYPE_NAME":
                    return "STRUCT"
            return "IDENT"
            
        return "IDENT"

    def highlight_ansi(self) -> str:
        """Returns a string with injected ANSI escape codes for terminals."""
        output = []
        last_end = 0
        for token in self.tokens:
            if token.type == TokenType.EOF:
                break
            # Append exact whitespace gaps between tokens
            output.append(self.source[last_end : token.start_pos])
            
            category = self._get_category(token)
            color_code = self.ANSI_COLORS.get(category, "")
            reset_code = self.ANSI_COLORS["RESET"]
            
            output.append(f"{color_code}{token.lexeme}{reset_code}")
            last_end = token.end_pos
            
        output.append(self.source[last_end:])
        return "".join(output)

    def highlight_html(self) -> str:
        """Returns a standalone, production-ready HTML document with embedded CSS."""
        output = []
        last_end = 0
        for token in self.tokens:
            if token.type == TokenType.EOF:
                break
            gap = self.source[last_end : token.start_pos]
            output.append(self._escape_html(gap))
            
            category = self._get_category(token)
            class_name = self.HTML_CLASSES.get(category, "")
            escaped_lexeme = self._escape_html(token.lexeme)
            
            if class_name:
                output.append(f'<span class="{class_name}">{escaped_lexeme}</span>')
            else:
                output.append(escaped_lexeme)
            last_end = token.end_pos
            
        output.append(self._escape_html(self.source[last_end:]))
        body_content = "".join(output)

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Compiler Syntax Highlighter</title>
<style>
    body {{ background: #1e1e1e; color: #d4d4d4; font-family: 'Consolas', 'Courier New', monospace; padding: 20px; }}
    pre {{ line-height: 1.5; }}
    .kw {{ color: #569cd6; font-weight: bold; }} /* Bold Blue */
    .type {{ color: #4ec9b0; }}                /* Teal/Cyan */
    .id {{ color: #d4d4d4; }}                  /* Variable default */
    .func {{ color: #dcdcaa; font-weight: bold; }} /* Gold Yellow for functions */
    .struct {{ color: #4ec9b0; font-weight: bold; }} /* Bright Green for Structs */
    .num {{ color: #b5cea8; }}                 /* Orange Literals */
    .str {{ color: #ce9178; }}                 /* Warm Green strings */
    .op {{ color: #a9a9a9; }}                  /* Light Gray operators */
    .com {{ color: #6a9955; font-style: italic; }} /* Dim Gray Italic comments */
    .err {{ text-decoration: underline red; }} /* Red Underline error representation */
</style>
</head>
<body>
<pre><code>{body_content}</code></pre>
</body>
</html>"""

    def _escape_html(self, text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")