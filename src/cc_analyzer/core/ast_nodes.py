from typing import List, Optional
from cc_analyzer.core.location import SourceLocation

class ASTNode:
    """Base class for all Abstract Syntax Tree nodes."""
    def __init__(self, location: SourceLocation):
        self.location = location
        self.type_annotation: Optional[str] = None  # Initially null, filled by Semantic Analyzer

    def accept(self, visitor):
        """Accept method for the Visitor pattern (useful for Highlighter, Symbol Table, etc.)."""
        raise NotImplementedError()


# --- Program & Declarations ---

class Program(ASTNode):
    """Represents the root of the AST containing all global declarations."""
    def __init__(self, declarations: List[ASTNode], location: SourceLocation):
        super().__init__(location)
        self.declarations = declarations

    def accept(self, visitor):
        return visitor.visit_program(self)


class VarDecl(ASTNode):
    """Represents a variable declaration: type_spec IDENT ('=' expr)? ';'"""
    def __init__(self, type_spec: str, identifier: str, initializer: Optional[ASTNode], location: SourceLocation):
        super().__init__(location)
        self.type_spec = type_spec  # e.g., "int", "float*", etc.
        self.identifier = identifier
        self.initializer = initializer

    def accept(self, visitor):
        return visitor.visit_var_decl(self)


class Param(ASTNode):
    """Represents a single parameter inside a function declaration: type_spec IDENT"""
    def __init__(self, type_spec: str, identifier: str, location: SourceLocation):
        super().__init__(location)
        self.type_spec = type_spec
        self.identifier = identifier

    def accept(self, visitor):
        return visitor.visit_param(self)


class FunctionDecl(ASTNode):
    """Represents a function declaration: type_spec IDENT '(' param_list? ')' block"""
    def __init__(self, type_spec: str, identifier: str, params: List[Param], block: 'Block', location: SourceLocation):
        super().__init__(location)
        self.type_spec = type_spec
        self.identifier = identifier
        self.params = params
        self.block = block

    def accept(self, visitor):
        return visitor.visit_function_decl(self)


class StructDecl(ASTNode):
    """Represents a struct definition: 'struct' IDENT '{' var_decl* '}' ';'"""
    def __init__(self, identifier: str, members: List[VarDecl], location: SourceLocation):
        super().__init__(location)
        self.identifier = identifier
        self.members = members

    def accept(self, visitor):
        return visitor.visit_struct_decl(self)


# --- Statements ---

class Block(ASTNode):
    """Represents a block of statements enclosed in curly braces: '{' statement* '}'"""
    def __init__(self, statements: List[ASTNode], location: SourceLocation):
        super().__init__(location)
        self.statements = statements

    def accept(self, visitor):
        return visitor.visit_block(self)


class IfStmt(ASTNode):
    """Represents an if statement with optional else branch: 'if' '(' expr ')' statement ('else' statement)?"""
    def __init__(self, condition: ASTNode, then_branch: ASTNode, else_branch: Optional[ASTNode], location: SourceLocation):
        super().__init__(location)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def accept(self, visitor):
        return visitor.visit_if_stmt(self)


class WhileStmt(ASTNode):
    """Represents a while loop: 'while' '(' expr ')' statement"""
    def __init__(self, condition: ASTNode, body: ASTNode, location: SourceLocation):
        super().__init__(location)
        self.condition = condition
        self.body = body

    def accept(self, visitor):
        return visitor.visit_while_stmt(self)


class ForStmt(ASTNode):
    """Represents a C-style for loop: 'for' '(' init_stmt cond_stmt expr? ')' statement"""
    def __init__(self, init: Optional[ASTNode], condition: Optional[ASTNode], increment: Optional[ASTNode], body: ASTNode, location: SourceLocation):
        super().__init__(location)
        self.init = init
        self.condition = condition
        self.increment = increment
        self.body = body

    def accept(self, visitor):
        return visitor.visit_for_stmt(self)


class ReturnStmt(ASTNode):
    """Represents a return statement: 'return' expr? ';'"""
    def __init__(self, expression: Optional[ASTNode], location: SourceLocation):
        super().__init__(location)
        self.expression = expression

    def accept(self, visitor):
        return visitor.visit_return_stmt(self)


class ExprStmt(ASTNode):
    """Represents an expression evaluated as a statement: expr? ';'"""
    def __init__(self, expression: Optional[ASTNode], location: SourceLocation):
        super().__init__(location)
        self.expression = expression

    def accept(self, visitor):
        return visitor.visit_expr_stmt(self)


# --- Expressions ---

class AssignmentExpr(ASTNode):
    """Represents an assignment expression: IDENT '=' assignment | ..."""
    def __init__(self, target: ASTNode, operator: str, value: ASTNode, location: SourceLocation):
        super().__init__(location)
        self.target = target          # Can be Identifier, MemberAccess, or ArrayAccess
        self.operator = operator      # '=', '+=', '-=', '*='
        self.value = value

    def accept(self, visitor):
        return visitor.visit_assignment_expr(self)


class BinaryExpr(ASTNode):
    """Represents binary operations: logical, equality, relational, additive, multiplicative."""
    def __init__(self, left: ASTNode, operator: str, right: ASTNode, location: SourceLocation):
        super().__init__(location)
        self.left = left
        self.operator = operator      # e.g., '+', '-', '*', '==', '&&', etc.
        self.right = right

    def accept(self, visitor):
        return visitor.visit_binary_expr(self)


class UnaryExpr(ASTNode):
    """Represents unary operations: '-', '!', '&', '*' (dereference)."""
    def __init__(self, operator: str, target: ASTNode, location: SourceLocation):
        super().__init__(location)
        self.operator = operator      # '-', '!', '&', '*'
        self.target = target

    def accept(self, visitor):
        return visitor.visit_unary_expr(self)


class CallExpr(ASTNode):
    """Represents a function call expression: callee '(' arg_list? ')'"""
    def __init__(self, callee: ASTNode, arguments: List[ASTNode], location: SourceLocation):
        super().__init__(location)
        self.callee = callee          # Typically an Identifier
        self.arguments = arguments

    def accept(self, visitor):
        return visitor.visit_call_expr(self)


class ArrayAccessExpr(ASTNode):
    """Represents array subscripting: target '[' index ']'"""
    def __init__(self, target: ASTNode, index: ASTNode, location: SourceLocation):
        super().__init__(location)
        self.target = target
        self.index = index

    def accept(self, visitor):
        return visitor.visit_array_access_expr(self)


class MemberAccessExpr(ASTNode):
    """Represents struct member access: target '.' member or target '->' member."""
    def __init__(self, target: ASTNode, operator: str, member: str, location: SourceLocation):
        super().__init__(location)
        self.target = target
        self.operator = operator      # '.' or '->'
        self.member = member          # The identifier name of the member

    def accept(self, visitor):
        return visitor.visit_member_access_expr(self)


# --- Primary / Literals ---

class Identifier(ASTNode):
    """Represents a variable, type, or function name."""
    def __init__(self, name: str, location: SourceLocation):
        super().__init__(location)
        self.name = name

    def accept(self, visitor):
        return visitor.visit_identifier(self)


class IntLiteral(ASTNode):
    """Represents an integer literal (decimal, hex, binary)."""
    def __init__(self, value: int, raw_value: str, location: SourceLocation):
        super().__init__(location)
        self.value = value            # Python integer
        self.raw_value = raw_value    # Original string (e.g. "0xFF")

    def accept(self, visitor):
        return visitor.visit_int_literal(self)


class FloatLiteral(ASTNode):
    """Represents a floating-point literal."""
    def __init__(self, value: float, raw_value: str, location: SourceLocation):
        super().__init__(location)
        self.value = value            # Python float
        self.raw_value = raw_value    # Original string (e.g. "3.14")

    def accept(self, visitor):
        return visitor.visit_float_literal(self)


class CharLiteral(ASTNode):
    """Represents a character literal."""
    def __init__(self, value: str, location: SourceLocation):
        super().__init__(location)
        self.value = value            # The single character or escaped representation

    def accept(self, visitor):
        return visitor.visit_char_literal(self)


class StringLiteral(ASTNode):
    """Represents a string literal."""
    def __init__(self, value: str, location: SourceLocation):
        super().__init__(location)
        self.value = value            # The raw or parsed string content

    def accept(self, visitor):
        return visitor.visit_string_literal(self)