import pytest
from cc_analyzer.analysis.language_detector import LanguageDetector

def test_detect_c_language():
    """Test 1: Verify standard C syntax structures yield a high C confidence score."""
    source = """
    #include <stdio.h>
    struct Node { int val; };
    void main() {
        printf("hello world\\n");
    }
    """
    results = LanguageDetector.detect(source)
    # The top predicted language must be C
    assert results[0][0] == "C"
    assert results[0][1] > 60.0


def test_detect_python_language():
    """Test 2: Verify Pythonic colon block patterns and keywords yield a high Python confidence."""
    source = """
    import sys
    
    def calculate_sum(a, b):
        if a > b:
            return a
        else:
            return b
    """
    results = LanguageDetector.detect(source)
    # The top predicted language must be Python
    assert results[0][0] == "Python"
    assert results[0][1] > 60.0


def test_detect_java_language():
    """Test 3: Verify Java OOP boilerplate matches Java signatures and reduces C probability."""
    source = """
    import java.util.Scanner;
    public class Main {
        public static void main(String[] args) {
            System.out.println("Hello Java");
        }
    }
    """
    results = LanguageDetector.detect(source)
    # The top predicted language must be Java
    assert results[0][0] == "Java"
    assert results[0][1] > 60.0


def test_detect_python_shebang():
    """Test 4: Verify Python shebang lines trigger immediate high Python score weights."""
    source = "#!/usr/bin/python\nprint('shebang test')"
    results = LanguageDetector.detect(source)
    assert results[0][0] == "Python"


def test_detect_empty_or_whitespace():
    """Test 5: Verify that empty strings or simple whitespaces gracefully return flat distributions."""
    results_empty = LanguageDetector.detect("")
    results_spaces = LanguageDetector.detect("   \n  \t ")
    
    # Assert equal distributions close to 33.3% for all candidate languages
    assert all(abs(conf - 33.3) < 1.0 for _, conf in results_empty)
    assert all(abs(conf - 33.3) < 1.0 for _, conf in results_spaces)


def test_detect_repl_command_output():
    """Test 6: Verify the detect command returns formatted output inside the REPL loop."""
    from cc_analyzer.presentation.repl import CommandLineRepl
    repl = CommandLineRepl()
    out = repl.run_command("detect void main() { printf(\"hi\"); }")
    
    assert "Language Detection Results" in out
    assert "- C:" in out
    assert "Match" in out