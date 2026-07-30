import pytest
from cc_analyzer.analysis.refactoring import RefactoringEngine

def test_goto_definition_and_hover():
    """Test 1: Verify goto-definition coordinates and documentation hover comment extraction."""
    source = """
    /* 
       Factorial documentation block 
    */
    int factorial(int n) {
        return n;
    }
    void main() {
        int x = factorial(5);
    }
    """
    engine = RefactoringEngine(source)
    
    # Hover or goto over 'factorial' call on line 9, col 17
    definition = engine.goto_definition(line=9, column=17)
    assert definition is not None
    assert definition["symbol"] == "factorial"
    assert definition["defined_at"]["line"] == 5  # Declared on line 5

    # Hover doc extraction check
    hover_info = engine.hover(line=9, column=17)
    assert hover_info is not None
    assert "Factorial documentation block" in hover_info["documentation"]


def test_find_all_references():
    """Test 2: Verify scope-aware references locate only the semantic matches."""
    source = """
    int n = 10;
    void main() {
        int n = 5; // shadows outer n
        n = n + 1;
    }
    """
    engine = RefactoringEngine(source)
    
    # Find all references of local 'n' inside main at line 4, col 13
    refs = engine.find_all_references(line=4, column=13)
    assert refs is not None
    assert len(refs) == 3  # Line 4 (declaration), Line 5 (left LHS), Line 5 (right RHS)
    assert all(r["line"] in (4, 5) for r in refs)


def test_rename_conflict_check():
    """Test 3: Verify rename conflicts raise exceptions when new name violates scoping."""
    source = """
    void main() {
        int x = 5;
        int y = 10;
    }
    """
    engine = RefactoringEngine(source)
    
    # Rename x (line 3, col 13) to 'y' -> Conflict inside same block!
    with pytest.raises(ValueError, match="Conflict Error"):
        engine.rename(line=3, column=13, new_name="y")


def test_rename_diff_generation():
    """Test 4: Verify a scope-aware rename generates a clean unified diff patch."""
    source = """int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}"""
    engine = RefactoringEngine(source)
    
    # Rename parameter 'n' (line 1, col 19) to 'number'
    diff = engine.rename(line=1, column=19, new_name="number")
    assert diff is not None
    assert "-int factorial(int n)" in diff
    assert "+int factorial(int number)" in diff
    assert "-    if (n <= 1) return 1;" in diff
    assert "+    if (number <= 1) return 1;" in diff


def test_hover_nonexistent_coordinates():
    """Test 5: Verify hovering over empty spacing/braces returns None."""
    source = "void main() { }"
    engine = RefactoringEngine(source)
    hover_info = engine.hover(line=1, column=14) # over '}'
    assert hover_info is None


def test_rename_shadow_conflict():
    """Test 6: Verify renaming triggers Shadow Conflict when it would capture outer bindings."""
    source = """
    int global_var = 5;
    void main() {
        int local_var = 10;
    }
    """
    engine = RefactoringEngine(source)
    # Renaming 'local_var' (line 4, col 13) to 'global_var' is a shadow conflict
    with pytest.raises(ValueError, match="Shadow Conflict"):
        engine.rename(line=4, column=13, new_name="global_var")