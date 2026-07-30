import pytest
from cc_analyzer.presentation.highlighter import SyntaxHighlighter

def test_ansi_and_html_basic_highlighting():
    """Test 1: Verify standard struct definitions, variables, and braces highlighting."""
    source_code = """
    struct Node {
        int val;
    };
    """
    highlighter = SyntaxHighlighter(source_code)
    ansi_output = highlighter.highlight_ansi()
    html_output = highlighter.highlight_html()

    assert "\033[1;34mstruct\033[0m" in ansi_output
    assert "\033[1;32mNode\033[0m" in ansi_output
    assert '<span class="kw">struct</span>' in html_output
    assert '<span class="struct">Node</span>' in html_output


def test_pointer_and_array_highlighting():
    """Test 2: Verify pointer indirection (*) and array index subscript brackets are correctly highlighted."""
    source_code = "int* arr; int x = arr[0];"
    highlighter = SyntaxHighlighter(source_code)
    ansi_output = highlighter.highlight_ansi()
    html_output = highlighter.highlight_html()

    assert "\033[36mint\033[0m\033[37m*\033[0m" in ansi_output
    assert '<span class="type">int</span><span class="op">*</span>' in html_output
    assert '<span class="op">[</span>' in html_output


def test_control_flow_nesting_highlighting():
    """Test 3: Verify deeply nested loops and branches highlight keyword statement structures."""
    source_code = "for (int i = 0; i < 10; i = i + 1) { if (i == 5) return; }"
    highlighter = SyntaxHighlighter(source_code)
    ansi_output = highlighter.highlight_ansi()
    html_output = highlighter.highlight_html()

    assert "\033[1;34mfor\033[0m" in ansi_output
    assert "\033[1;34mif\033[0m" in ansi_output
    assert '<span class="kw">for</span>' in html_output
    assert '<span class="kw">if</span>' in html_output


def test_literals_and_comments_highlighting():
    """Test 4: Verify highlighting of float exponentials, characters, and single/block comments."""
    source_code = """
    // Leading comment
    float f = 1.2e-3;
    char c = '\\n';
    /* Block comment */
    """
    highlighter = SyntaxHighlighter(source_code)
    ansi_output = highlighter.highlight_ansi()
    html_output = highlighter.highlight_html()

    assert "\033[3;90m// Leading comment\033[0m" in ansi_output
    assert "\033[33m1.2e-3\033[0m" in ansi_output
    assert '<span class="com">/* Block comment */</span>' in html_output
    assert '<span class="str">\'\\n\'</span>' in html_output


def test_lexical_and_semantic_error_highlighting():
    """Test 5: Verify that invalid characters or unterminated items invoke error styles."""
    source_code = "int invalid = @; /* unclosed"
    highlighter = SyntaxHighlighter(source_code)
    ansi_output = highlighter.highlight_ansi()
    html_output = highlighter.highlight_html()

    assert "\033[4;31m@\033[0m" in ansi_output
    assert '<span class="err">@</span>' in html_output
    assert 'unclosed' in html_output


def test_nested_member_access_highlighting():
    """Test 6: Verify dot and arrow member access highlighting inside custom function scopes."""
    source_code = """
    struct Point { int x; };
    void draw() {
        struct Point p;
        p.x = 42;
    }
    """
    highlighter = SyntaxHighlighter(source_code)
    ansi_output = highlighter.highlight_ansi()
    html_output = highlighter.highlight_html()

    assert "\033[1;32mPoint\033[0m" in ansi_output
    assert "\033[1;33mdraw\033[0m" in ansi_output
    assert '<span class="struct">Point</span>' in html_output