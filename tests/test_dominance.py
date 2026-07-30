import pytest
from cc_analyzer.core.lexer import Lexer
from cc_analyzer.core.parser import Parser
from cc_analyzer.core.ast_nodes import FunctionDecl
from cc_analyzer.analysis.cfg import CFGBuilder
from cc_analyzer.analysis.dominance import DominanceAnalyzer

def parse_function(source: str) -> FunctionDecl:
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    program = parser.parse()
    return program.declarations[0]


def test_dominance_straight_line():
    """Test 1: Verify straight-line code block is dominated by ENTRY and dominates EXIT."""
    source = """
    void main() {
        int x = 5;
    }
    """
    func_decl = parse_function(source)
    cfg = CFGBuilder().build("main", func_decl)
    analyzer = DominanceAnalyzer(cfg)
    analyzer.analyze()

    start_block = next(b for b in cfg.blocks if b.id == 1)
    
    # start_block is immediately dominated by ENTRY (0)
    assert analyzer.get_idom(start_block) == cfg.entry
    # EXIT (-1) is immediately dominated by start_block
    assert analyzer.get_idom(cfg.exit) == start_block


def test_dominance_if_branching():
    """Test 2: Verify idoms and dominance frontiers (DF) inside standard if-else split branches."""
    source = """
    void check(int cond) {
        if (cond) {
            int a = 1;
        } else {
            int b = 2;
        }
    }
    """
    func_decl = parse_function(source)
    cfg = CFGBuilder().build("check", func_decl)
    analyzer = DominanceAnalyzer(cfg)
    analyzer.analyze()

    start_block = next(b for b in cfg.blocks if b.id == 1) # 'func_start' containing the condition
    then_block = next(b for b in cfg.blocks if b.label == "then_branch")
    else_block = next(b for b in cfg.blocks if b.label == "else_branch")
    merge_block = next(b for b in cfg.blocks if b.label == "if_merge")

    # then_branch and else_branch are both immediately dominated by the split start_block
    assert analyzer.get_idom(then_block) == start_block
    assert analyzer.get_idom(else_block) == start_block
    
    # merge_block is also immediately dominated by start_block
    assert analyzer.get_idom(merge_block) == start_block

    # DF of then_branch and else_branch contain merge_block because they are join points
    assert merge_block in analyzer.get_dominance_frontier(then_block)
    assert merge_block in analyzer.get_dominance_frontier(else_block)


def test_dominance_while_loop():
    """Test 3: Verify dominance loopback relationships inside while loops."""
    source = """
    void loop() {
        while (1) {
            int x = 5;
        }
    }
    """
    func_decl = parse_function(source)
    cfg = CFGBuilder().build("loop", func_decl)
    analyzer = DominanceAnalyzer(cfg)
    analyzer.analyze()

    cond_block = next(b for b in cfg.blocks if b.label == "while_cond")
    body_block = next(b for b in cfg.blocks if b.label == "while_body")
    merge_block = next(b for b in cfg.blocks if b.label == "while_merge")

    # condition block dominates loop body and merge blocks
    assert analyzer.get_idom(body_block) == cond_block
    assert analyzer.get_idom(merge_block) == cond_block

    # DF of body_block contains cond_block (due to loopback edge)
    assert cond_block in analyzer.get_dominance_frontier(body_block)


def test_dominance_for_loop():
    """Test 4: Verify dominance low-link properties inside C89-style for loops."""
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
    analyzer = DominanceAnalyzer(cfg)
    analyzer.analyze()

    cond_block = next(b for b in cfg.blocks if b.label == "for_cond")
    body_block = next(b for b in cfg.blocks if b.label == "for_body")
    incr_block = next(b for b in cfg.blocks if b.label == "for_incr")

    assert analyzer.get_idom(body_block) == cond_block
    # Increment block is dominated by body_block
    assert analyzer.get_idom(incr_block) == body_block

    # DF of incr_block must contain the loop condition block
    assert cond_block in analyzer.get_dominance_frontier(incr_block)


def test_idom_path_evaluations():
    """Test 5: Verify immediate dominator evaluations using the full Lengauer-Tarjan algorithm."""
    source = """
    void main() {
        int x = 1;
        if (x) {
            int y = 2;
        }
    }
    """
    func_decl = parse_function(source)
    cfg = CFGBuilder().build("main", func_decl)
    analyzer = DominanceAnalyzer(cfg)
    analyzer.analyze()

    # Checks structural validation of the full tree structure
    tree = analyzer.get_dominator_tree_structure()
    assert cfg.entry in tree
    assert len(tree[cfg.entry]) == 1  # Links only to block 1


def test_dominator_repl_command_output():
    """Test 6: Verify the show-dominators output inside the command REPL interface."""
    from cc_analyzer.presentation.repl import CommandLineRepl
    repl = CommandLineRepl()
    
    source = """
    void check(int cond) {
        if (cond) {
            int a = 1;
        }
    }
    """
    repl.run_command(f"load {source}")
    out = repl.run_command("show-dominators check")
    
    assert "Dominance Analysis for function 'check'" in out
    assert "Immediate Dominators" in out
    assert "Dominance Frontier" in out
    assert "Dominator Tree Structure" in out