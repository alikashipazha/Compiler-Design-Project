from typing import Dict, List, Optional, Tuple
from cc_analyzer.core.location import SourceLocation

class Symbol:
    """Represents a registered name in the Symbol Table (Section 5.1)."""
    def __init__(
        self, 
        name: str, 
        kind: str,  # 'variable', 'function', 'type', 'parameter', 'struct_member'
        type_: str,  # Type expression representation (e.g. 'int', 'struct Point*', 'void')
        definition_loc: SourceLocation,
        signature: Optional[Tuple[List[str], str]] = None  # (parameter_types, return_type) for functions
    ):
        self.name = name
        self.kind = kind
        self.type = type_
        self.definition_loc = definition_loc
        self.signature = signature
        self.references: List[SourceLocation] = []
        self.is_initialized: bool = False
        self.is_used: bool = False

    def __repr__(self) -> str:
        return f"Symbol({self.name}, kind={self.kind}, type={self.type}, loc={self.definition_loc})"


class Scope:
    """Represents a lexical scope in a hierarchical scope tree (Section 5.1.1)."""
    def __init__(self, name: str, parent: Optional['Scope'] = None, is_struct_scope: bool = False):
        self.name = name                      # For debugging / identification (e.g. 'global', 'factorial_body')
        self.parent = parent                  # Enclosing scope
        self.children: List['Scope'] = []     # Nested scopes
        self.symbols: Dict[str, Symbol] = {}  # Symbol storage for this scope level
        self.is_struct_scope = is_struct_scope # True if this scope defines struct fields

        if parent:
            parent.children.append(self)

    def define(self, symbol: Symbol) -> bool:
        """Defines a symbol in the current local scope. 
        Returns False if the symbol already exists locally (duplicate declaration)."""
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Looks up a symbol ONLY in the current local scope level."""
        return self.symbols.get(name)

    def lookup(self, name: str) -> Optional[Symbol]:
        """Performs lexical scope resolution, walking outward to the global scope (Section 5.2)."""
        # 1. Search current scope
        symbol = self.symbols.get(name)
        if symbol is not None:
            return symbol
        
        # 2. Walk outward to enclosing scopes
        if self.parent is not None:
            return self.parent.lookup(name)
            
        return None

    def print_tree(self, indent: int = 0):
        """Helper to output the scope tree hierarchy for documentation/debugging."""
        prefix = "  " * indent
        print(f"{prefix}Scope: {self.name}")
        for symbol in self.symbols.values():
            sig_info = f" with sig {symbol.signature}" if symbol.signature else ""
            print(f"{prefix}  [{symbol.kind}] '{symbol.name}' : {symbol.type}{sig_info} at {symbol.definition_loc}")
        for child in self.children:
            child.print_tree(indent + 1)