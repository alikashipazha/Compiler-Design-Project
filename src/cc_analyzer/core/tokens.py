from enum import Enum
from cc_analyzer.core.location import SourceLocation

class TokenType(Enum):
    # Keywords
    KW_IF = "if"
    KW_ELSE = "else"
    KW_WHILE = "while"
    KW_FOR = "for"
    KW_RETURN = "return"
    KW_STRUCT = "struct"
    KW_INT = "int"
    KW_FLOAT = "float"
    KW_CHAR = "char"
    KW_VOID = "void"
    KW_DOUBLE = "double"

    # Identifiers & Literals
    IDENT = "IDENTIFIER"
    LIT_INT = "INTEGER_LITERAL"
    LIT_FLOAT = "FLOAT_LITERAL"
    LIT_CHAR = "CHAR_LITERAL"
    LIT_STRING = "STRING_LITERAL"

    # Operators
    OP_ADD = "+"
    OP_SUB = "-"
    OP_MUL = "*"
    OP_DIV = "/"
    OP_MOD = "%"
    OP_ASSIGN = "="
    OP_ADD_ASSIGN = "+="
    OP_SUB_ASSIGN = "-="
    OP_MUL_ASSIGN = "*="
    OP_EQ = "=="
    OP_NE = "!="
    OP_LT = "<"
    OP_GT = ">"
    OP_LE = "<="
    OP_GE = ">="
    OP_AND = "&&"
    OP_OR = "||"
    OP_NOT = "!"
    OP_BIT_AND = "&"
    OP_ARROW = "->"
    OP_DOT = "."

    # Delimiters
    LBRACE = "{"
    RBRACE = "}"
    LPAREN = "("
    RPAREN = ")"
    LBRACK = "["
    RBRACK = "]"
    SEMICOLON = ";"
    COMMA = ","

    # Special Tokens
    COMMENT_SINGLE = "COMMENT_SINGLE"
    COMMENT_BLOCK = "COMMENT_BLOCK"
    INVALID = "INVALID"
    EOF = "EOF"


class Token:
    """A single token scanned by the Lexical Analyzer."""
    def __init__(self, type_: TokenType, lexeme: str, location: SourceLocation, start_pos: int, end_pos: int):
        self.type = type_
        self.lexeme = lexeme
        self.location = location
        self.start_pos = start_pos
        self.end_pos = end_pos

    def __repr__(self) -> str:
        return f"Token({self.type.name}, '{self.lexeme}', {self.location})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Token):
            return NotImplemented
        return (self.type == other.type and 
                self.lexeme == other.lexeme and 
                self.location == other.location)