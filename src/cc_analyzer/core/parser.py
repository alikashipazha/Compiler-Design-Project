from typing import List, Optional, Set
from cc_analyzer.core.location import SourceLocation
from cc_analyzer.core.tokens import TokenType, Token
from cc_analyzer.core.ast_nodes import (
    ASTNode, Program, VarDecl, Param, FunctionDecl, StructDecl, Block,
    IfStmt, WhileStmt, ForStmt, ReturnStmt, ExprStmt, AssignmentExpr,
    BinaryExpr, UnaryExpr, CallExpr, ArrayAccessExpr, MemberAccessExpr,
    Identifier, IntLiteral, FloatLiteral, CharLiteral, StringLiteral
)

class ParseError(Exception):
    """Custom exception used to break the recursive call stack on syntax errors 
    and initiate panic-mode recovery."""
    pass


class Parser:
    """Hand-written LL(k) Recursive Descent Parser for a subset of C."""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        self.errors: List[str] = []
        self.struct_names: Set[str] = set()  # Captures custom struct names for highlighter mapping
        self.last_error_index: int = -1      # Progress-tracker to prevent infinite loops during recovery

    def parse(self) -> Program:
        """Entry point: program ::= declaration* EOF"""
        declarations = []
        start_loc = self._peek().location
        
        while not self._is_at_end():
            try:
                decl = self._declaration()
                if decl is not None:
                    declarations.append(decl)
            except ParseError:
                self._synchronize()
                
        return Program(declarations, start_loc)

    # --- Parser Helper Utilities ---

    def _peek(self, offset: int = 0) -> Token:
        pos = self.current + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[pos]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _check(self, type_: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == type_

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _match(self, *types: TokenType) -> bool:
        for type_ in types:
            if self._check(type_):
                self._advance()
                return True
        return False

    def _consume(self, type_: TokenType, message: str) -> Token:
        if self._check(type_):
            return self._advance()
        raise self._error(self._peek(), message)

    def _error(self, token: Token, message: str) -> ParseError:
        err_msg = f"Error at {token.location}: {message} (got '{token.lexeme}')"
        self.errors.append(err_msg)
        return ParseError()

    def _synchronize(self):
        """Panic-mode recovery (Section 4.3.3): skips tokens until a synchronization point 
        (like semicolon) is consumed or stops immediately before a declaration/statement keyword."""
        # Progress-tracking guard: If we haven't made progress since the last error, force-advance once
        if self.current == self.last_error_index:
            self._advance()
        self.last_error_index = self.current

        while not self._is_at_end():
            # Stop if we peek at any statement or declaration starter
            if self._peek().type in (
                TokenType.KW_IF, TokenType.KW_WHILE, TokenType.KW_FOR, TokenType.KW_RETURN,
                TokenType.KW_STRUCT, TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_CHAR,
                TokenType.KW_VOID, TokenType.KW_DOUBLE, TokenType.LBRACE
            ):
                return
            
            token = self._advance()
            if token.type == TokenType.SEMICOLON:
                return

    # --- Grammar Translation Rules ---

    def _declaration(self) -> Optional[ASTNode]:
        """declaration ::= function_decl | var_decl | struct_decl"""
        if self._check(TokenType.KW_STRUCT):
            # Differentiate struct declaration 'struct Node { ...' from a struct variable
            if self._peek(1).type == TokenType.IDENT and self._peek(2).type == TokenType.LBRACE:
                return self._struct_decl()
            
        ts = self._type_spec()
        ident_token = self._consume(TokenType.IDENT, "Expected identifier after type specification")
        
        # Distinguish function from variable using 1-token lookahead '('
        if self._check(TokenType.LPAREN):
            return self._function_decl(ts, ident_token)
        else:
            return self._var_decl(ts, ident_token)

    def _type_spec(self) -> str:
        """type_spec ::= ('struct' IDENT | 'int' | 'float' | 'char' | 'void' | 'double') '*'*"""
        type_parts = []
        
        if self._match(TokenType.KW_STRUCT):
            type_parts.append("struct")
            ident = self._consume(TokenType.IDENT, "Expected struct name in type specifier")
            type_parts.append(ident.lexeme)
            # Register the custom struct type name for semantic highlighting
            self.struct_names.add(ident.lexeme)
        elif self._match(TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_CHAR, TokenType.KW_VOID, TokenType.KW_DOUBLE):
            type_parts.append(self._previous().lexeme)
        else:
            raise self._error(self._peek(), "Expected type specification")

        # Pointers (e.g. int*, int**)
        while self._match(TokenType.OP_MUL):
            type_parts.append("*")
            
        return " ".join(type_parts) if "struct" in type_parts else "".join(type_parts)

    def _var_decl(self, type_spec: str, ident_token: Token) -> VarDecl:
        """var_decl ::= type_spec IDENT ('=' expr)? ';'"""
        initializer = None
        if self._match(TokenType.OP_ASSIGN):
            initializer = self._expr()
        self._consume(TokenType.SEMICOLON, "Expected ';' after variable declaration")
        return VarDecl(type_spec, ident_token.lexeme, initializer, ident_token.location)

    def _function_decl(self, type_spec: str, ident_token: Token) -> FunctionDecl:
        """function_decl ::= type_spec IDENT '(' param_list? ')' block"""
        self._consume(TokenType.LPAREN, "Expected '(' after function name")
        params = []
        if not self._check(TokenType.RPAREN):
            params = self._param_list()
        self._consume(TokenType.RPAREN, "Expected ')' after parameters")
        func_block = self._block()
        return FunctionDecl(type_spec, ident_token.lexeme, params, func_block, ident_token.location)

    def _param_list(self) -> List[Param]:
        """param_list ::= param (',' param)*"""
        params = [self._param()]
        while self._match(TokenType.COMMA):
            params.append(self._param())
        return params

    def _param(self) -> Param:
        """param ::= type_spec IDENT"""
        ts = self._type_spec()
        ident = self._consume(TokenType.IDENT, "Expected parameter identifier")
        return Param(ts, ident.lexeme, ident.location)

    def _struct_decl(self) -> StructDecl:
        """struct_decl ::= 'struct' IDENT '{' var_decl* '}' ';'"""
        struct_token = self._consume(TokenType.KW_STRUCT, "Expected 'struct'")
        ident = self._consume(TokenType.IDENT, "Expected struct identifier")
        # Register the custom declared struct name
        self.struct_names.add(ident.lexeme)
        self._consume(TokenType.LBRACE, "Expected '{' to start struct body")
        
        members = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            try:
                ts = self._type_spec()
                mem_ident = self._consume(TokenType.IDENT, "Expected member identifier")
                members.append(self._var_decl(ts, mem_ident))
            except ParseError:
                self._synchronize()
                
        self._consume(TokenType.RBRACE, "Expected '}' after struct body")
        self._consume(TokenType.SEMICOLON, "Expected ';' after struct declaration")
        return StructDecl(ident.lexeme, members, struct_token.location)

    def _block(self) -> Block:
        """block ::= '{' statement* '}'"""
        lbrace_token = self._consume(TokenType.LBRACE, "Expected '{' to open block")
        statements = []
        
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            try:
                stmt = self._statement()
                if stmt is not None:
                    statements.append(stmt)
            except ParseError:
                self._synchronize()
                
        self._consume(TokenType.RBRACE, "Expected '}' to close block")
        return Block(statements, lbrace_token.location)

    def _statement(self) -> Optional[ASTNode]:
        """statement ::= if_stmt | while_stmt | for_stmt | return_stmt | expr_stmt | block | var_decl"""
        if self._check(TokenType.LBRACE):
            return self._block()
        if self._match(TokenType.KW_IF):
            return self._if_stmt()
        if self._match(TokenType.KW_WHILE):
            return self._while_stmt()
        if self._match(TokenType.KW_FOR):
            return self._for_stmt()
        if self._match(TokenType.KW_RETURN):
            return self._return_stmt()
            
        # Distinguish local var_decl from expr_stmt
        if self._peek().type in (
            TokenType.KW_STRUCT, TokenType.KW_INT, TokenType.KW_FLOAT, 
            TokenType.KW_CHAR, TokenType.KW_VOID, TokenType.KW_DOUBLE
        ):
            ts = self._type_spec()
            ident = self._consume(TokenType.IDENT, "Expected local variable identifier")
            return self._var_decl(ts, ident)
            
        return self._expr_stmt()

    def _if_stmt(self) -> IfStmt:
        """if_stmt ::= 'if' '(' expr ')' statement ('else' statement)?"""
        if_loc = self._previous().location
        self._consume(TokenType.LPAREN, "Expected '(' after 'if'")
        condition = self._expr()
        self._consume(TokenType.RPAREN, "Expected ')' after if condition")
        then_branch = self._statement()
        
        else_branch = None
        if self._match(TokenType.KW_ELSE):
            else_branch = self._statement()
            
        return IfStmt(condition, then_branch, else_branch, if_loc)

    def _while_stmt(self) -> WhileStmt:
        """while_stmt ::= 'while' '(' expr ')' statement"""
        while_loc = self._previous().location
        self._consume(TokenType.LPAREN, "Expected '(' after 'while'")
        condition = self._expr()
        self._consume(TokenType.RPAREN, "Expected ')' after condition")
        body = self._statement()
        return WhileStmt(condition, body, while_loc)

    def _for_stmt(self) -> ForStmt:
        """for_stmt ::= 'for' '(' expr_stmt expr_stmt expr? ')' statement"""
        for_loc = self._previous().location
        self._consume(TokenType.LPAREN, "Expected '(' after 'for'")
        init = self._expr_stmt()
        cond = self._expr_stmt()
        condition_expr = cond.expression if isinstance(cond, ExprStmt) else None
        
        increment = None
        if not self._check(TokenType.RPAREN):
            increment = self._expr()
            
        self._consume(TokenType.RPAREN, "Expected ')' after for clauses")
        body = self._statement()
        return ForStmt(init, condition_expr, increment, body, for_loc)

    def _return_stmt(self) -> ReturnStmt:
        """return_stmt ::= 'return' expr? ';'"""
        ret_loc = self._previous().location
        expression = None
        if not self._check(TokenType.SEMICOLON):
            expression = self._expr()
        self._consume(TokenType.SEMICOLON, "Expected ';' after return expression")
        return ReturnStmt(expression, ret_loc)

    def _expr_stmt(self) -> ExprStmt:
        """expr_stmt ::= expr? ';'"""
        loc = self._peek().location
        expression = None
        if not self._check(TokenType.SEMICOLON):
            expression = self._expr()
        self._consume(TokenType.SEMICOLON, "Expected ';' after expression statement")
        return ExprStmt(expression, loc)

    def _expr(self) -> ASTNode:
        """expr ::= assignment"""
        return self._assignment()

    def _assignment(self) -> ASTNode:
        """assignment ::= IDENT ('='|'+='|'-='|'*=') assignment | logical_or"""
        expr_node = self._logical_or()
        
        if self._match(TokenType.OP_ASSIGN, TokenType.OP_ADD_ASSIGN, TokenType.OP_SUB_ASSIGN, TokenType.OP_MUL_ASSIGN):
            op_token = self._previous()
            value = self._assignment()
            
            # Verify assignment is targeting a valid lvalue
            if isinstance(expr_node, (Identifier, MemberAccessExpr, ArrayAccessExpr)):
                return AssignmentExpr(expr_node, op_token.lexeme, value, op_token.location)
            else:
                self._error(op_token, "Invalid assignment target")
                
        return expr_node

    def _logical_or(self) -> ASTNode:
        """logical_or ::= logical_and ('||' logical_and)*"""
        node = self._logical_and()
        while self._match(TokenType.OP_OR):
            op = self._previous()
            right = self._logical_and()
            node = BinaryExpr(node, op.lexeme, right, op.location)
        return node

    def _logical_and(self) -> ASTNode:
        """logical_and ::= equality ('&&' equality)*"""
        node = self._equality()
        while self._match(TokenType.OP_AND):
            op = self._previous()
            right = self._equality()
            node = BinaryExpr(node, op.lexeme, right, op.location)
        return node

    def _equality(self) -> ASTNode:
        """equality ::= relational (('=='|'!=') relational)*"""
        node = self._relational()
        while self._match(TokenType.OP_EQ, TokenType.OP_NE):
            op = self._previous()
            right = self._relational()
            node = BinaryExpr(node, op.lexeme, right, op.location)
        return node

    def _relational(self) -> ASTNode:
        """relational ::= additive (('<'|'>'|'<='|'>=') additive)*"""
        node = self._additive()
        while self._match(TokenType.OP_LT, TokenType.OP_GT, TokenType.OP_LE, TokenType.OP_GE):
            op = self._previous()
            right = self._additive()
            node = BinaryExpr(node, op.lexeme, right, op.location)
        return node

    def _additive(self) -> ASTNode:
        """additive ::= multiplicative (('+'|'-') multiplicative)*"""
        node = self._multiplicative()
        while self._match(TokenType.OP_ADD, TokenType.OP_SUB):
            op = self._previous()
            right = self._multiplicative()
            node = BinaryExpr(node, op.lexeme, right, op.location)
        return node

    def _multiplicative(self) -> ASTNode:
        """multiplicative ::= unary (('*'|'/'|'%') unary)*"""
        node = self._unary()
        while self._match(TokenType.OP_MUL, TokenType.OP_DIV, TokenType.OP_MOD):
            op = self._previous()
            right = self._unary()
            node = BinaryExpr(node, op.lexeme, right, op.location)
        return node

    def _unary(self) -> ASTNode:
        """unary ::= ('-'|'!'|'&'|'*') unary | postfix"""
        if self._match(TokenType.OP_SUB, TokenType.OP_NOT, TokenType.OP_BIT_AND, TokenType.OP_MUL):
            op = self._previous()
            right = self._unary()
            return UnaryExpr(op.lexeme, right, op.location)
        return self._postfix()

    def _postfix(self) -> ASTNode:
        """postfix ::= primary ('[' expr ']' | '(' arg_list? ')' | '.' IDENT | '->' IDENT)*"""
        node = self._primary()
        
        while True:
            if self._match(TokenType.LBRACK):
                op_loc = self._previous().location
                index = self._expr()
                self._consume(TokenType.RBRACK, "Expected ']' after array index")
                node = ArrayAccessExpr(node, index, op_loc)
            elif self._match(TokenType.LPAREN):
                op_loc = self._previous().location
                args = []
                if not self._check(TokenType.RPAREN):
                    args = self._arg_list()
                self._consume(TokenType.RPAREN, "Expected ')' after function arguments")
                node = CallExpr(node, args, op_loc)
            elif self._match(TokenType.OP_DOT, TokenType.OP_ARROW):
                op_token = self._previous()
                member = self._consume(TokenType.IDENT, "Expected member name after access operator")
                node = MemberAccessExpr(node, op_token.lexeme, member.lexeme, op_token.location)
            else:
                break
                
        return node

    def _primary(self) -> ASTNode:
        """primary ::= INT | FLOAT | STRING | CHAR | IDENT | '(' expr ')'"""
        if self._match(TokenType.LIT_INT):
            token = self._previous()
            raw = token.lexeme
            if raw.startswith(("0x", "0X")):
                val = int(raw, 16)
            elif raw.startswith(("0b", "0B")):
                val = int(raw, 2)
            else:
                val = int(raw)
            return IntLiteral(val, raw, token.location)
            
        if self._match(TokenType.LIT_FLOAT):
            token = self._previous()
            return FloatLiteral(float(token.lexeme), token.lexeme, token.location)
            
        if self._match(TokenType.LIT_STRING):
            token = self._previous()
            return StringLiteral(token.lexeme, token.location)
            
        if self._match(TokenType.LIT_CHAR):
            token = self._previous()
            return CharLiteral(token.lexeme, token.location)
            
        if self._match(TokenType.IDENT):
            token = self._previous()
            return Identifier(token.lexeme, token.location)
            
        if self._match(TokenType.LPAREN):
            node = self._expr()
            self._consume(TokenType.RPAREN, "Expected ')' after expression")
            return node
            
        raise self._error(self._peek(), "Expected expression")

    def _arg_list(self) -> List[ASTNode]:
        """arg_list ::= expr (',' expr)*"""
        args = [self._expr()]
        while self._match(TokenType.COMMA):
            args.append(self._expr())
        return args