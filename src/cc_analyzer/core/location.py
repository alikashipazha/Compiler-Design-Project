class SourceLocation:
    """Represents a position in the source code file for error reporting and IDE features."""
    def __init__(self, line: int, column: int):
        self.line = line
        self.column = column

    def __repr__(self) -> str:
        return f"{self.line}:{self.column}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SourceLocation):
            return NotImplemented
        return self.line == other.line and self.column == other.column