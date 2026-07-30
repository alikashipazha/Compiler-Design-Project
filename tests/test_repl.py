import pytest
from cc_analyzer.presentation.repl import CommandLineRepl

def test_repl_help_and_exit():
    """Test 1: Verify help usage menu and exit output text."""
    repl = CommandLineRepl()
    help_out = repl.run_command("help")
    assert "CC-IDE REPL Interactive Command Helper" in help_out

    exit_out = repl.run_command("exit")
    assert "Exiting CC-IDE REPL" in exit_out


def test_repl_load_code():
    """Test 2: Verify source code loading commands."""
    repl = CommandLineRepl()
    load_out = repl.run_command("load int x = 5;")
    assert "Successfully loaded" in load_out

    err_out = repl.run_command("load int x = ;")
    assert "Successfully loaded" in err_out # Parser handles syntax errors, so load is successful!


def test_repl_goto_def_and_hover():
    """Test 3: Verify goto-definition and hover interactive commands."""
    repl = CommandLineRepl()
    source = """
    int x = 5;
    void f() {
        int y = x;
    }
    """
    repl.run_command(f"load {source}")
    
    # Hover over 'x' on line 4, col 17
    hover_out = repl.run_command("hover 4 17")
    assert "int x" in hover_out

    # Goto-def over 'x'
    def_out = repl.run_command("goto-def 4 17")
    assert "Defined: 2:9" in def_out


def test_repl_find_refs_and_rename():
    """Test 4: Verify find-references and global rename refactoring commands."""
    repl = CommandLineRepl()
    source = """
    int val = 10;
    void main() {
        int x = val;
    }
    """
    repl.run_command(f"load {source}")

    # Find-refs over 'val' at line 2, col 9
    refs_out = repl.run_command("find-refs 2 9")
    assert "Found 2 references" in refs_out

    # Rename 'val' to 'value'
    rename_out = repl.run_command("rename 2 9 value")
    assert "-    int val = 10;" in rename_out
    assert "+    int value = 10;" in rename_out


def test_repl_cfg_visualization():
    """Test 5: Verify CFG block statement structure printer command."""
    repl = CommandLineRepl()
    source = """
    int calc(int x) {
        if (x) return 1;
        return 0;
    }
    """
    repl.run_command(f"load {source}")
    cfg_out = repl.run_command("show-cfg calc")
    
    assert "CFG for function 'calc'" in cfg_out
    assert "Block 1 [func_start]" in cfg_out
    assert "Successors" in cfg_out


def test_repl_callgraph_and_dead_code():
    """Test 6: Verify program-wide Call Graph, cycle recursions, and dead code reporting."""
    repl = CommandLineRepl()
    source = """
    void unused() {}
    void main() {
        int x;
        int y = x; // Uninitialized read!
    }
    """
    repl.run_command(f"load {source}")

    cg_out = repl.run_command("show-callgraph")
    assert "Program-Wide Call Graph" in cg_out

    dead_out = repl.run_command("dead-code")
    assert "Dead Functions" in dead_out
    assert "unused" in dead_out
    assert "Uninitialized Reads" in dead_out