import pytest
from cc_analyzer.core.location import SourceLocation
from cc_analyzer.core.lexer import Lexer
from cc_analyzer.core.parser import Parser
from cc_analyzer.semantics.type_checker import TypeChecker
from cc_analyzer.core.ast_nodes import Program

@pytest.fixture
def checker():
    return TypeChecker()

def parse_source(source: str) -> Program:
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    return parser.parse()


def test_duplicate_declarations(checker):
    """Verify that defining the same variable twice in the same block scope triggers an Error."""
    source = """
    void main() {
        int x = 5;
        float x = 2.0; 
    }
    """
    ast = parse_source(source)
    diags = checker.check(ast)
    errors = [d for d in diags if d["severity"] == "Error"]
    assert any("Duplicate declaration of symbol 'x'" in d["message"] for d in errors)


def test_variable_shadowing(checker):
    """Verify that declaring an inner variable with the same name as an outer variable triggers a Warning."""
    source = """
    int x = 10;
    void main() {
        int x = 5; 
    }
    """
    ast = parse_source(source)
    diags = checker.check(ast)
    warnings = [d for d in diags if d["severity"] == "Warning"]
    assert any("Variable 'x' shadows an outer declaration" in d["message"] for d in warnings)


def test_precision_loss_warning(checker):
    """Verify that assigning a float/double literal to an int variable triggers a precision-loss Warning."""
    source = """
    void main() {
        int x = 3.14; 
    }
    """
    ast = parse_source(source)
    diags = checker.check(ast)
    warnings = [d for d in diags if d["severity"] == "Warning"]
    assert any("double to int conversion loses precision" in d["message"] for d in warnings)


def test_incompatible_pointer_assignment(checker):
    """Verify that implicitly assigning a numeric literal to a pointer variable triggers an Error."""
    source = """
    void main() {
        int* ptr = 5; 
    }
    """
    ast = parse_source(source)
    diags = checker.check(ast)
    errors = [d for d in diags if d["severity"] == "Error"]
    assert any("Cannot implicitly assign 'int' to pointer" in d["message"] for d in errors)


def test_function_call_argument_mismatch(checker):
    """Verify that calling a function with incorrect argument count triggers an Error."""
    source = """
    int foo(int a, float b) {
        return a;
    }
    void main() {
        int x = foo(5); 
    }
    """
    ast = parse_source(source)
    diags = checker.check(ast)
    errors = [d for d in diags if d["severity"] == "Error"]
    assert any("expected 2 arguments" in d["message"] for d in errors)


def test_return_type_mismatch(checker):
    """Verify that returning a value from a function declared as void triggers an Error."""
    source = """
    void foo() {
        return 5; 
    }
    """
    ast = parse_source(source)
    diags = checker.check(ast)
    errors = [d for d in diags if d["severity"] == "Error"]
    assert any("Value return inside void" in d["message"] for d in errors)


def test_uninitialized_variable_warning(checker):
    """Verify that reading a variable before any assignment has occurred triggers an initialization Warning."""
    source = """
    void main() {
        int x;
        int y = x + 5; 
    }
    """
    ast = parse_source(source)
    diags = checker.check(ast)
    warnings = [d for d in diags if d["severity"] == "Warning"]
    assert any("Variable 'x' may be used uninitialized" in d["message"] for d in warnings)


def test_struct_member_access(checker):
    """Verify that accessing non-existent members on custom structs triggers a semantic Error."""
    source = """
    struct Point {
        int x;
        int y;
    };
    void main() {
        struct Point p;
        p.x = 5;
        p.z = 10; 
    }
    """
    ast = parse_source(source)
    diags = checker.check(ast)
    errors = [d for d in diags if d["severity"] == "Error"]
    assert any("has no member named 'z'" in d["message"] for d in errors)