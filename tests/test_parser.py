import pytest
from cc_analyzer.core.location import SourceLocation
from cc_analyzer.core.tokens import TokenType, Token
from cc_analyzer.core.lexer import Lexer
from cc_analyzer.core.parser import Parser
from cc_analyzer.core.ast_nodes import (
    VarDecl, StructDecl, FunctionDecl, Block, ReturnStmt, BinaryExpr,
    IfStmt, WhileStmt, MemberAccessExpr, ArrayAccessExpr, Identifier,
    IntLiteral, FloatLiteral
)

def test_variable_declarations():
    """Verify standard variable declarations, pointer notations, and struct variables."""
    source = """
    int x = 42;
    float* ptr;
    struct Node n;
    """
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    program = parser.parse()
    
    assert len(parser.errors) == 0
    assert len(program.declarations) == 3
    
    # 1. int x = 42;
    decl1 = program.declarations[0]
    assert isinstance(decl1, VarDecl)
    assert decl1.type_spec == "int"
    assert decl1.identifier == "x"
    assert isinstance(decl1.initializer, IntLiteral)
    assert decl1.initializer.value == 42
    
    # 2. float* ptr;
    decl2 = program.declarations[1]
    assert isinstance(decl2, VarDecl)
    assert decl2.type_spec == "float*"
    assert decl2.identifier == "ptr"
    assert decl2.initializer is None

    # 3. struct Node n;
    decl3 = program.declarations[2]
    assert isinstance(decl3, VarDecl)
    assert decl3.type_spec == "struct Node"
    assert decl3.identifier == "n"


def test_struct_declaration():
    """Verify that custom structs are parsed correctly, capturing all internal members."""
    source = """
    struct Point {
        int x;
        int y;
    };
    """
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    program = parser.parse()
    
    assert len(parser.errors) == 0
    assert len(program.declarations) == 1
    
    decl = program.declarations[0]
    assert isinstance(decl, StructDecl)
    assert decl.identifier == "Point"
    assert len(decl.members) == 2
    assert decl.members[0].identifier == "x"
    assert decl.members[0].type_spec == "int"
    assert decl.members[1].identifier == "y"
    assert decl.members[1].type_spec == "int"


def test_function_declaration():
    """Verify function signatures, param types, and complete function body blocks."""
    source = """
    void process(int code, float val) {
        return;
    }
    """
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    program = parser.parse()
    
    assert len(parser.errors) == 0
    assert len(program.declarations) == 1
    
    decl = program.declarations[0]
    assert isinstance(decl, FunctionDecl)
    assert decl.type_spec == "void"
    assert decl.identifier == "process"
    assert len(decl.params) == 2
    assert decl.params[0].identifier == "code"
    assert decl.params[0].type_spec == "int"
    assert decl.params[1].identifier == "val"
    assert decl.params[1].type_spec == "float"
    
    assert isinstance(decl.block, Block)
    assert len(decl.block.statements) == 1
    assert isinstance(decl.block.statements[0], ReturnStmt)


def test_operator_precedence():
    """Check mathematical precedence: 1 + 2 * 3 must parse as 1 + (2 * 3)."""
    source = "int res = 1 + 2 * 3;"
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    program = parser.parse()
    
    decl = program.declarations[0]
    assert isinstance(decl.initializer, BinaryExpr)
    root_expr = decl.initializer
    assert root_expr.operator == "+"
    
    # Left must be literal 1
    assert isinstance(root_expr.left, IntLiteral)
    assert root_expr.left.value == 1
    
    # Right must be binary expression (2 * 3)
    assert isinstance(root_expr.right, BinaryExpr)
    assert root_expr.right.operator == "*"
    assert isinstance(root_expr.right.left, IntLiteral)
    assert root_expr.right.left.value == 2
    assert isinstance(root_expr.right.right, IntLiteral)
    assert root_expr.right.right.value == 3


def test_nested_statements():
    """Test standard nested flow constructs such as if-else blocks containing while loops."""
    source = """
    void loop() {
        if (x < 10) {
            while (x > 0) {
                x = x - 1;
            }
        } else {
            return;
        }
    }
    """
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    program = parser.parse()
    
    assert len(parser.errors) == 0
    func = program.declarations[0]
    assert isinstance(func.block.statements[0], IfStmt)
    
    if_stmt = func.block.statements[0]
    assert isinstance(if_stmt.condition, BinaryExpr)
    assert if_stmt.condition.operator == "<"
    
    # Then branch must contain a WhileStmt inside its Block
    assert isinstance(if_stmt.then_branch, Block)
    while_stmt = if_stmt.then_branch.statements[0]
    assert isinstance(while_stmt, WhileStmt)
    
    # Else branch must contain a ReturnStmt inside its Block
    assert isinstance(if_stmt.else_branch, Block)
    assert isinstance(if_stmt.else_branch.statements[0], ReturnStmt)


def test_postfix_and_member_access():
    """Verify priority and AST structures for array subscripting followed by struct member accesses."""
    source = "int r = arr[i]->val;"
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    program = parser.parse()
    
    decl = program.declarations[0]
    expr = decl.initializer
    
    # arr[i]->val should yield: MemberAccessExpr(ArrayAccessExpr(arr, i), "->", "val")
    assert isinstance(expr, MemberAccessExpr)
    assert expr.operator == "->"
    assert expr.member == "val"
    
    assert isinstance(expr.target, ArrayAccessExpr)
    assert isinstance(expr.target.target, Identifier)
    assert expr.target.target.name == "arr"
    assert isinstance(expr.target.index, Identifier)
    assert expr.target.index.name == "i"


def test_error_recovery():
    """Verify that panic-mode synchronization localizes parser errors 
    and lets parsing proceed on subsequent valid statements."""
    source = """
    int x = ;       // Error: missing expr
    int y = 42;     // Valid
    int z = 10      // Error: missing semicolon
    int a = 100;    // Valid
    """
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    program = parser.parse()
    
    # Must capture exactly 2 syntax errors
    assert len(parser.errors) == 2
    # Must successfully parse 'y' and 'a' declarations despite intervening errors
    assert len(program.declarations) == 2
    assert program.declarations[0].identifier == "y"
    assert program.declarations[1].identifier == "a"