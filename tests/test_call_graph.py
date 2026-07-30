import pytest
from cc_analyzer.core.lexer import Lexer
from cc_analyzer.core.parser import Parser
from cc_analyzer.analysis.call_graph import CallGraph

def build_call_graph(source: str) -> CallGraph:
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    program = parser.parse()
    cg = CallGraph()
    cg.build(program)
    return cg


def test_direct_and_transitive_calls():
    """Test 1: Verify direct and transitive call site reachability (callers & callees)."""
    source = """
    void c() {}
    void b() { c(); }
    void a() { b(); }
    void main() { a(); }
    """
    cg = build_call_graph(source)
    
    assert cg.get_callees("b") == {"c"}
    assert cg.get_callers("c") == {"b"}
    
    # Transitive reachable callees
    assert cg.get_transitive_callees("a") == {"b", "c"}
    assert cg.get_transitive_callers("c") == {"b", "a", "main"}


def test_cycle_recursion_detection():
    """Test 2: Verify cycle detection identifies both direct and indirect (mutual) recursions."""
    source = """
    void direct() { direct(); }
    
    void alice() { bob(); }
    void bob() { alice(); }
    
    void main() { direct(); alice(); }
    """
    cg = build_call_graph(source)
    
    assert cg.is_recursive("direct") is True
    assert cg.is_recursive("alice") is True
    assert cg.is_recursive("bob") is True
    assert cg.is_recursive("main") is False


def test_dead_functions():
    """Test 3: Verify that functions never called transitively from 'main' are detected as dead."""
    source = """
    void live() {}
    void dead_helper() {}
    void main() { live(); }
    """
    cg = build_call_graph(source)
    
    dead = cg.get_dead_functions()
    assert "dead_helper" in dead
    assert "live" not in dead
    assert "main" not in dead


def test_strongly_connected_components_tarjan():
    """Test 4: Verify that SCC algorithms correctly group mutually recursive function cycles."""
    source = """
    void f1() { f2(); }
    void f2() { f1(); }
    void f3() { f1(); }
    """
    cg = build_call_graph(source)
    sccs = cg.get_sccs()
    
    # f1 and f2 are mutually recursive cycle, hence forming an SCC together
    cyclic_scc = next(scc for scc in sccs if "f1" in scc)
    assert set(cyclic_scc) == {"f1", "f2"}


def test_empty_program_call_graph():
    """Test 5: Verify that the call graph engine handles empty programs without crashing."""
    source = ""
    cg = build_call_graph(source)
    assert len(cg.nodes) == 0
    assert len(cg.get_dead_functions()) == 0


def test_complex_call_reachability():
    """Test 6: Verify reachability on a complex DAG program structure."""
    source = """
    void d() {}
    void c() { d(); }
    void b() { d(); }
    void a() { b(); c(); }
    void main() { a(); }
    """
    cg = build_call_graph(source)
    assert cg.get_transitive_callees("a") == {"b", "c", "d"}
    assert "d" in cg.get_transitive_callees("main")