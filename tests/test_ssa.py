import pytest
from cc_analyzer.core.lexer import Lexer
from cc_analyzer.core.parser import Parser
from cc_analyzer.core.ast_nodes import FunctionDecl
from cc_analyzer.analysis.cfg import CFGBuilder
from cc_analyzer.analysis.dominance import DominanceAnalyzer
from cc_analyzer.analysis.ssa import SSATransformer

def parse_function(source: str) -> FunctionDecl:
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    program = parser.parse()
    return program.declarations[0]


def test_ssa_straight_line():
    """Test 1: Verify straight-line code variables get subscript 1 and increments appropriately."""
    source = """
    void main() {
        int x = 5;
        x = x + 1;
    }
    """
    func_decl = parse_function(source)
    cfg = CFGBuilder().build("main", func_decl)
    
    dom = DominanceAnalyzer(cfg)
    dom.analyze()

    transformer = SSATransformer(cfg, dom)
    transformer.transform()

    # Find start block statements
    start_block = next(b for b in cfg.blocks if b.id == 1)
    stmts = transformer.ssa_blocks[start_block]
    
    # x declared as x_1, then reassigned as x_2 using x_1 on RHS
    assert "int x_1 = 5" in stmts[0]
    assert "x_2 = (x_1 + 1)" in stmts[1]


def test_ssa_if_branch_phi():
    """Test 2: Verify if-else branching variables place a phi-function in the merge block."""
    source = """
    void check(int cond) {
        int x = 0;
        if (cond) {
            x = 1;
        } else {
            x = 2;
        }
        int y = x;
    }
    """
    func_decl = parse_function(source)
    cfg = CFGBuilder().build("check", func_decl)
    
    dom = DominanceAnalyzer(cfg)
    dom.analyze()

    transformer = SSATransformer(cfg, dom)
    transformer.transform()

    # The 'if_merge' block must contain a phi-function for 'x'
    merge_block = next(b for b in cfg.blocks if b.label == "if_merge")
    phis = transformer.phi_functions[merge_block]
    
    # Formula expected: x_4 = phi(x_2, x_3)
    assert any("x_4 = phi" in phi for phi in phis)


def test_ssa_while_loop_phi():
    """Test 3: Verify loopback assignments place a phi-function in the while loop condition header."""
    source = """
    void loop() {
        int i = 0;
        while (1) {
            i = i + 1;
        }
    }
    """
    func_decl = parse_function(source)
    cfg = CFGBuilder().build("loop", func_decl)
    
    dom = DominanceAnalyzer(cfg)
    dom.analyze()

    transformer = SSATransformer(cfg, dom)
    transformer.transform()

    cond_block = next(b for b in cfg.blocks if b.label == "while_cond")
    phis = transformer.phi_functions[cond_block]
    
    # Formula expected: i_2 = phi(i_1, i_3) where i_1 is init, i_3 is loopback increment
    assert any("i_2 = phi" in phi for phi in phis)


def test_ssa_for_loop_phi():
    """Test 4: Verify C89-style for loops place appropriate phi-functions in the loop condition header."""
    source = """
    void loop() {
        int i;
        for (i = 0; i < 10; i = i + 1) {
            int y = i;
        }
    }
    """
    func_decl = parse_function(source)
    cfg = CFGBuilder().build("loop", func_decl)
    
    dom = DominanceAnalyzer(cfg)
    dom.analyze()

    transformer = SSATransformer(cfg, dom)
    transformer.transform()

    cond_block = next(b for b in cfg.blocks if b.label == "for_cond")
    phis = transformer.phi_functions[cond_block]
    
    # Formula expected: i_3 = phi(i_2, i_4)
    assert any("i_3 = phi" in phi for phi in phis)


def test_ssa_multiple_vars():
    """Test 5: Verify that multiple independent variables are subscripted without interference."""
    source = """
    void main() {
        int x = 1;
        int y = 2;
        x = x + y;
    }
    """
    func_decl = parse_function(source)
    cfg = CFGBuilder().build("main", func_decl)
    
    dom = DominanceAnalyzer(cfg)
    dom.analyze()

    transformer = SSATransformer(cfg, dom)
    transformer.transform()

    start_block = next(b for b in cfg.blocks if b.id == 1)
    stmts = transformer.ssa_blocks[start_block]
    
    assert "int x_1 = 1" in stmts[0]
    assert "int y_1 = 2" in stmts[1]
    assert "x_2 = (x_1 + y_1)" in stmts[2]


def test_ssa_repl_command_output():
    """Test 6: Verify the show-ssa command returns formatted representations inside the REPL loop."""
    from cc_analyzer.presentation.repl import CommandLineRepl
    repl = CommandLineRepl()
    
    source = """
    void main() {
        int x = 5;
    }
    """
    repl.run_command(f"load {source}")
    out = repl.run_command("show-ssa main")
    
    assert "Static Single Assignment (SSA Form) for function 'main'" in out
    assert "Block 1 [func_start]" in out
    assert "- int x_1 = 5" in out