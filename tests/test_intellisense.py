import pytest
from cc_analyzer.semantics.intellisense import IntellisenseEngine

@pytest.fixture
def source_code():
    return """
    struct Node {
        int val;
        struct Node* next;
    };

    int calculate(int factor) {
        struct Node n;
        struct Node* ptr = &n;
        n.val = 10;
        ptr->val = 20;
        int err = @; // Lexical error
        return factor;
    }
    """

def test_hover_function_decl(source_code):
    """Test 1: Verify hover information over function name correctly reveals its signature."""
    engine = IntellisenseEngine(source_code)
    # Line 7, Col 9 is within the word 'calculate'
    hover = engine.get_hover_info(line=7, column=9)
    assert hover is not None
    assert hover["name"] == "calculate"
    assert hover["kind"] == "function"
    assert "int calculate(int)" in hover["detail"]


def test_hover_parameter(source_code):
    """Test 2: Verify hover information over function parameter retrieves its C type specifier."""
    engine = IntellisenseEngine(source_code)
    # Parameter 'factor' starts exactly at Column 23
    hover = engine.get_hover_info(line=7, column=23)
    assert hover is not None
    assert hover["name"] == "factor"
    assert hover["kind"] == "parameter"
    assert hover["detail"] == "int factor"


def test_hover_struct_variable(source_code):
    """Test 3: Verify hover information over pointer variables declares its pointer structure."""
    engine = IntellisenseEngine(source_code)
    # Line 9, Col 22 is over 'ptr'
    hover = engine.get_hover_info(line=9, column=22)
    assert hover is not None
    assert hover["name"] == "ptr"
    assert hover["kind"] == "variable"
    # Matches the exact C spacing formatting produced by the compiler: "struct Node * ptr"
    assert hover["detail"] == "struct Node * ptr"


def test_member_completion_dot(source_code):
    """Test 4: Verify auto-completion suggestions after dot '.' show all valid struct fields."""
    engine = IntellisenseEngine(source_code)
    # Line 10, Col 11 is immediately after 'n.'
    completions = engine.get_completions(line=10, column=11)
    fields = [c["label"] for c in completions if c["kind"] == "Field"]
    assert "val" in fields
    assert "next" in fields


def test_member_completion_arrow(source_code):
    """Test 5: Verify auto-completion suggestions after arrow '->' resolve struct pointer fields."""
    engine = IntellisenseEngine(source_code)
    # Line 11, Col 13 is immediately after 'ptr->'
    completions = engine.get_completions(line=11, column=13)
    fields = [c["label"] for c in completions if c["kind"] == "Field"]
    assert "val" in fields
    assert "next" in fields


def test_hover_empty_whitespace(source_code):
    """Test 6: Verify that hovering over an empty whitespace coordinate gracefully returns None."""
    engine = IntellisenseEngine(source_code)
    # Line 7, Col 2 is empty leading spacing
    hover = engine.get_hover_info(line=7, column=2)
    assert hover is None


def test_diagnostic_aggregation(source_code):
    """Test 7: Verify that the engine correctly aggregates lexer, parser, and semantic diagnostics."""
    engine = IntellisenseEngine(source_code)
    diagnostics = engine.get_diagnostics()
    errors = [d for d in diagnostics if d["severity"] == "Error"]
    assert any("Lexical error: invalid token '@'" in d["message"] for d in errors)