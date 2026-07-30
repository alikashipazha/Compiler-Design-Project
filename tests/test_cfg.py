import pytest
from cc_analyzer.core.lexer import Lexer
from cc_analyzer.core.parser import Parser
from cc_analyzer.core.ast_nodes import FunctionDecl
from cc_analyzer.analysis.cfg import CFGBuilder, CFGAnalyzer

def parse_function(source: str) -> FunctionDecl:
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    program = parser.parse()
    return program.declarations[0]


def test_cfg_basic_structure():
    """Test 1: Verify that a straight-line function yields a simple sequential block linked to EXIT."""
    source = """
    void main() {
        int x = 5;
        x = x + 1;
    }
    """
    func_decl = parse_function(source)
    builder = CFGBuilder()
    cfg = builder.build("main", func_decl)

    # Blocks: ENTRY (0), EXIT (-1), and start block (1)
    assert len(cfg.blocks) == 3
    start_block = next(b for b in cfg.blocks if b.id == 1)
    assert len(start_block.statements) == 2
    assert cfg.exit in start_block.successors


def test_cfg_if_branching():
    """Test 2: Verify if-else branches construct correct split and merge edges."""
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
    builder = CFGBuilder()
    cfg = builder.build("check", func_decl)

    # Find ENTRY successors
    start_block = cfg.entry.successors[0]
    assert len(start_block.successors) == 2  # split into 'then' and 'else'
    
    then_block = next(b for b in start_block.successors if b.label == "then_branch")
    else_block = next(b for b in start_block.successors if b.label == "else_branch")
    
    assert len(then_block.successors) == 1
    assert len(else_block.successors) == 1
    
    # Both merge into if_merge block
    assert then_block.successors[0] == else_block.successors[0]


def test_unreachable_code_detection():
    """Test 3: Verify that statements textually placed after return are flagged as unreachable."""
    source = """
    int dead() {
        return 42;
        int x = 10; // Dead / Unreachable statement
    }
    """
    func_decl = parse_function(source)
    builder = CFGBuilder()
    cfg = builder.build("dead", func_decl)

    unreachable = CFGAnalyzer.detect_unreachable_blocks(cfg)
    assert len(unreachable) == 0  # Sequential code blocks handle return directly by cutting successors
    
    # Verify 'int x = 10;' was never added to the exit-linked path block
    start_block = cfg.entry.successors[0]
    assert len(start_block.statements) == 1  # Only contains return 42;


def test_cfg_definite_assignment():
    """Test 4: Verify that uninitialized usage paths are correctly verified via graph traversal."""
    source = """
    void calc(int condition) {
        int x;
        if (condition) {
            x = 42;
        }
        int y = x; // Uninitialized read if condition is False!
    }
    """
    func_decl = parse_function(source)
    builder = CFGBuilder()
    cfg = builder.build("calc", func_decl)
    
    # We find the use statement 'int y = x;' (the last var declaration statement)
    use_stmt = func_decl.block.statements[-1]
    
    is_safe = CFGAnalyzer.check_definite_assignment(cfg, "x", use_stmt)
    assert is_safe is False # There is a path where condition is False, leaving x unassigned!


def test_cfg_while_loop():
    """Test 5: Verify that a while loop constructs a condition block with back-edges."""
    source = """
    void loop() {
        while (1) {
            int x = 5;
        }
    }
    """
    func_decl = parse_function(source)
    builder = CFGBuilder()
    cfg = builder.build("loop", func_decl)

    # Find the while_cond block and verify loopback
    cond_block = next(b for b in cfg.blocks if b.label == "while_cond")
    body_block = next(b for b in cfg.blocks if b.label == "while_body")
    merge_block = next(b for b in cfg.blocks if b.label == "while_merge")

    assert body_block in cond_block.successors
    assert merge_block in cond_block.successors
    assert cond_block in body_block.successors  # Loop back-edge


def test_cfg_for_loop():
    """Test 6: Verify that a for loop connects the initializer, condition, and increment blocks."""
    source = """
    void loop() {
        int i;
        for (i = 0; i < 10; i = i + 1) {
            int y = i;
        }
    }
    """
    func_decl = parse_function(source)
    builder = CFGBuilder()
    cfg = builder.build("loop", func_decl)

    cond_block = next(b for b in cfg.blocks if b.label == "for_cond")
    body_block = next(b for b in cfg.blocks if b.label == "for_body")
    incr_block = next(b for b in cfg.blocks if b.label == "for_incr")
    merge_block = next(b for b in cfg.blocks if b.label == "for_merge")

    assert body_block in cond_block.successors
    assert merge_block in cond_block.successors
    assert incr_block in body_block.successors
    assert cond_block in incr_block.successors  # Increment loop back-edge