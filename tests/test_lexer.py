import pytest
from cc_analyzer.core.location import SourceLocation
from cc_analyzer.core.tokens import TokenType, Token
from cc_analyzer.core.lexer import Lexer

def test_keywords():
    """Verify that all C subset keywords are tokenized with their respective types."""
    source = "if else while for return struct int float char void double"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    expected = [
        TokenType.KW_IF, TokenType.KW_ELSE, TokenType.KW_WHILE, TokenType.KW_FOR,
        TokenType.KW_RETURN, TokenType.KW_STRUCT, TokenType.KW_INT, TokenType.KW_FLOAT,
        TokenType.KW_CHAR, TokenType.KW_VOID, TokenType.KW_DOUBLE, TokenType.EOF
    ]
    assert [t.type for t in tokens] == expected


def test_identifiers():
    """Verify that valid identifiers are scanned correctly and distinct from keywords."""
    source = "myVar _count x123 _abc_12"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    expected_lexemes = ["myVar", "_count", "x123", "_abc_12", ""]
    assert [t.lexeme for t in tokens] == expected_lexemes
    assert all(t.type == TokenType.IDENT for t in tokens[:-1])


def test_integer_literals():
    """Test standard decimal, hexadecimal, and binary integer formats."""
    source = "42 0xFF 0b1010 0X1a"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    expected_types = [
        TokenType.LIT_INT, TokenType.LIT_INT, TokenType.LIT_INT, TokenType.LIT_INT, TokenType.EOF
    ]
    expected_lexemes = ["42", "0xFF", "0b1010", "0X1a", ""]
    assert [t.type for t in tokens] == expected_types
    assert [t.lexeme for t in tokens] == expected_lexemes


def test_float_literals():
    """Test standard float, scientific exponent float, and dot-leading float formats."""
    source = "3.14 1.0e-5 .5 .5e2 0.0"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    expected_types = [
        TokenType.LIT_FLOAT, TokenType.LIT_FLOAT, TokenType.LIT_FLOAT, 
        TokenType.LIT_FLOAT, TokenType.LIT_FLOAT, TokenType.EOF
    ]
    expected_lexemes = ["3.14", "1.0e-5", ".5", ".5e2", "0.0", ""]
    assert [t.type for t in tokens] == expected_types
    assert [t.lexeme for t in tokens] == expected_lexemes


def test_string_literals():
    """Test valid strings with escape characters and recovery for unterminated strings."""
    source = '"hello" "world\\n" "unterminated'
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    # Valid string
    assert tokens[0].type == TokenType.LIT_STRING
    assert tokens[0].lexeme == '"hello"'
    
    # Escape characters inside string
    assert tokens[1].type == TokenType.LIT_STRING
    assert tokens[1].lexeme == '"world\\n"'
    
    # Unterminated string yields INVALID
    assert tokens[2].type == TokenType.INVALID
    assert tokens[2].lexeme == '"unterminated'


def test_character_literals():
    """Test character literal validation, including escape sequences and invalid inputs."""
    source = "'a' '\\t' 'ab' '\\x'"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    # Valid char
    assert tokens[0].type == TokenType.LIT_CHAR
    assert tokens[0].lexeme == "'a'"
    
    # Valid escaped char
    assert tokens[1].type == TokenType.LIT_CHAR
    assert tokens[1].lexeme == "'\\t'"
    
    # Invalid multi-character literal
    assert tokens[2].type == TokenType.INVALID
    assert tokens[2].lexeme == "'ab'"
    
    # Invalid escape sequence
    assert tokens[3].type == TokenType.INVALID
    assert tokens[3].lexeme == "'\\x'"


def test_operators_and_delimiters():
    """Test multi-character and single-character operators and delimiters."""
    source = "-> <= == != && || + - * / % = < > & . { } ( ) [ ] ; ,"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    expected_types = [
        TokenType.OP_ARROW, TokenType.OP_LE, TokenType.OP_EQ, TokenType.OP_NE,
        TokenType.OP_AND, TokenType.OP_OR, TokenType.OP_ADD, TokenType.OP_SUB,
        TokenType.OP_MUL, TokenType.OP_DIV, TokenType.OP_MOD, TokenType.OP_ASSIGN,
        TokenType.OP_LT, TokenType.OP_GT, TokenType.OP_BIT_AND, TokenType.OP_DOT,
        TokenType.LBRACE, TokenType.RBRACE, TokenType.LPAREN, TokenType.RPAREN,
        TokenType.LBRACK, TokenType.RBRACK, TokenType.SEMICOLON, TokenType.COMMA,
        TokenType.EOF
    ]
    assert [t.type for t in tokens] == expected_types


def test_comments():
    """Test that valid comments are skipped and unterminated block comments yield an INVALID token."""
    source = """
    int x = 1; // single line comment
    /* multi-line
       comment */
    int y = 2;
    /* unterminated comment
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    expected_types = [
        TokenType.KW_INT, TokenType.IDENT, TokenType.OP_ASSIGN, TokenType.LIT_INT, TokenType.SEMICOLON,
        TokenType.KW_INT, TokenType.IDENT, TokenType.OP_ASSIGN, TokenType.LIT_INT, TokenType.SEMICOLON,
        TokenType.INVALID, TokenType.EOF
    ]
    assert [t.type for t in tokens] == expected_types
    
    # Check that the unterminated block comment is reported as INVALID with exact text
    invalid_comment_token = [t for t in tokens if t.type == TokenType.INVALID][0]
    assert invalid_comment_token.lexeme.startswith("/* unterminated")


def test_location_tracking():
    """Test that lines and columns are tracked correctly, accounting for whitespaces and newlines."""
    source = "int x;\n  y = 10;"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    # 'int' -> Row 1, Col 1
    assert tokens[0].location == SourceLocation(1, 1)
    # 'x' -> Row 1, Col 5
    assert tokens[1].location == SourceLocation(1, 5)
    # ';' -> Row 1, Col 6
    assert tokens[2].location == SourceLocation(1, 6)
    # 'y' -> Row 2, Col 3 (due to 2 leading spaces on line 2)
    assert tokens[3].location == SourceLocation(2, 3)