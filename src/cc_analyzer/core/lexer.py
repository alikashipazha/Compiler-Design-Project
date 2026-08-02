from typing import List, Optional
from cc_analyzer.core.location import SourceLocation
from cc_analyzer.core.tokens import TokenType, Token

class Lexer:
    """Hand-written DFA-based Lexical Analyzer for a subset of C."""
    
    KEYWORDS = {
        "if": TokenType.KW_IF,
        "else": TokenType.KW_ELSE,
        "while": TokenType.KW_WHILE,
        "for": TokenType.KW_FOR,
        "return": TokenType.KW_RETURN,
        "struct": TokenType.KW_STRUCT,
        "int": TokenType.KW_INT,
        "float": TokenType.KW_FLOAT,
        "char": TokenType.KW_CHAR,
        "void": TokenType.KW_VOID,
        "double": TokenType.KW_DOUBLE,
    }

    def __init__(self, source_code: str):
        self.source = source_code
        self.position = 0
        self.line = 1
        self.column = 1
        self.length = len(source_code)

    def _peek(self, offset: int = 0) -> Optional[str]:
        pos = self.position + offset
        if pos >= self.length:
            return None
        return self.source[pos]

    def _advance(self) -> Optional[str]:
        if self.position >= self.length:
            return None
        char = self.source[self.position]
        self.position += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def _current_location(self) -> SourceLocation:
        return SourceLocation(self.line, self.column)

    def tokenize(self, keep_comments: bool = False) -> List[Token]:
        """Scan the entire source code and return a list of tokens ending with EOF."""
        tokens = []
        while self.position < self.length:
            token = self.next_token(keep_comments)
            if token is not None:
                tokens.append(token)
        tokens.append(Token(TokenType.EOF, "", self._current_location(), self.position, self.position))
        return tokens

    def next_token(self, keep_comments: bool = False) -> Optional[Token]:
        """Scan the next token from the source."""
        self._skip_whitespace_and_comments(keep_comments)
        
        if self.position >= self.length:
            return None

        loc = self._current_location()
        start_pos = self.position
        char = self._peek()

        # Handle comments if keep_comments is True (otherwise they would be skipped above)
        if char == '/' and self._peek(1) == '/':
            lexeme_chars = [self._advance(), self._advance()]
            while self.position < self.length and self._peek() != '\n':
                lexeme_chars.append(self._advance())
            return Token(TokenType.COMMENT_SINGLE, "".join(lexeme_chars), loc, start_pos, self.position)

        if char == '/' and self._peek(1) == '*':
            lexeme_chars = [self._advance(), self._advance()]
            terminated = False
            while self.position < self.length:
                if self._peek() == '*' and self._peek(1) == '/':
                    lexeme_chars.append(self._advance())  # '*'
                    lexeme_chars.append(self._advance())  # '/'
                    terminated = True
                    break
                lexeme_chars.append(self._advance())
            tt = TokenType.COMMENT_BLOCK if terminated else TokenType.INVALID
            return Token(tt, "".join(lexeme_chars), loc, start_pos, self.position)

        # 1. Identifiers and Keywords
        if char.isalpha() or char == '_':
            return self._scan_identifier_or_keyword(start_pos, loc)

        # 2. Numbers (Integer or Float Literals starting with digit)
        if char.isdigit():
            return self._scan_number(start_pos, loc)

        # 3. Float Literals starting with a dot (e.g. .5, .5e-2)
        if char == '.' and self._peek(1) is not None and self._peek(1).isdigit():
            return self._scan_number_starting_with_dot(start_pos, loc)

        # 4. String Literals
        if char == '"':
            return self._scan_string(start_pos, loc)

        # 5. Character Literals
        if char == "'":
            return self._scan_char(start_pos, loc)

        # 6. Operators and Delimiters
        char = self._advance()
        next_char = self._peek()

        # Two-character operators (Longest Match)
        if char == '-' and next_char == '>':
            self._advance()
            return Token(TokenType.OP_ARROW, "->", loc, start_pos, self.position)
        if char == '=' and next_char == '=':
            self._advance()
            return Token(TokenType.OP_EQ, "==", loc, start_pos, self.position)
        if char == '!' and next_char == '=':
            self._advance()
            return Token(TokenType.OP_NE, "!=", loc, start_pos, self.position)
        if char == '<' and next_char == '=':
            self._advance()
            return Token(TokenType.OP_LE, "<=", loc, start_pos, self.position)
        if char == '>' and next_char == '=':
            self._advance()
            return Token(TokenType.OP_GE, ">=", loc, start_pos, self.position)
        if char == '+' and next_char == '=':
            self._advance()
            return Token(TokenType.OP_ADD_ASSIGN, "+=", loc, start_pos, self.position)
        if char == '-' and next_char == '=':
            self._advance()
            return Token(TokenType.OP_SUB_ASSIGN, "-=", loc, start_pos, self.position)
        if char == '*' and next_char == '=':
            self._advance()
            return Token(TokenType.OP_MUL_ASSIGN, "*=", loc, start_pos, self.position)
        if char == '&' and next_char == '&':
            self._advance()
            return Token(TokenType.OP_AND, "&&", loc, start_pos, self.position)
        if char == '|' and next_char == '|':
            self._advance()
            return Token(TokenType.OP_OR, "||", loc, start_pos, self.position)

        single_tokens = {
            '+': TokenType.OP_ADD,
            '-': TokenType.OP_SUB,
            '*': TokenType.OP_MUL,
            '/': TokenType.OP_DIV,
            '%': TokenType.OP_MOD,
            '=': TokenType.OP_ASSIGN,
            '<': TokenType.OP_LT,
            '>': TokenType.OP_GT,
            '&': TokenType.OP_BIT_AND,
            '.': TokenType.OP_DOT,
            '{': TokenType.LBRACE,
            '}': TokenType.RBRACE,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '[': TokenType.LBRACK,
            ']': TokenType.RBRACK,
            ';': TokenType.SEMICOLON,
            ',': TokenType.COMMA,
            '!': TokenType.OP_NOT, # <--- Added standalone NOT operator
        }

        if char in single_tokens:
            return Token(single_tokens[char], char, loc, start_pos, self.position)

        # Lexical Error Recovery: emit INVALID token and continue
        return Token(TokenType.INVALID, char, loc, start_pos, self.position)

    def _skip_whitespace_and_comments(self, keep_comments: bool):
        while self.position < self.length:
            char = self._peek()
            if char in (' ', '\t', '\r', '\n'):
                self._advance()
            elif char == '#':
                # C Preprocessor Directive (Section 7 - Bonus): skip the entire preprocessor line
                self._advance() # consume '#'
                while self.position < self.length and self._peek() != '\n':
                    self._advance()
            elif char == '/' and self._peek(1) == '/' and not keep_comments:
                self._advance()
                self._advance()
                while self.position < self.length and self._peek() != '\n':
                    self._advance()
            elif char == '/' and self._peek(1) == '*' and not keep_comments:
                temp_pos = self.position + 2
                terminated = False
                while temp_pos < self.length:
                    if self.source[temp_pos] == '*' and temp_pos + 1 < self.length and self.source[temp_pos+1] == '/':
                        terminated = True
                        break
                    temp_pos += 1
                
                if terminated:
                    self._advance()
                    self._advance()
                    while self.position < temp_pos:
                        self._advance()
                    self._advance()
                    self._advance()
                else:
                    break
            else:
                break

    def _scan_identifier_or_keyword(self, start_pos: int, loc: SourceLocation) -> Token:
        lexeme_chars = []
        while self.position < self.length:
            char = self._peek()
            if char.isalnum() or char == '_':
                lexeme_chars.append(self._advance())
            else:
                break
        lexeme = "".join(lexeme_chars)
        token_type = self.KEYWORDS.get(lexeme, TokenType.IDENT)
        return Token(token_type, lexeme, loc, start_pos, self.position)

    def _scan_number(self, start_pos: int, loc: SourceLocation) -> Token:
        lexeme_chars = []
        char = self._peek()
        
        # Hexadecimal
        if char == '0' and self._peek(1) in ('x', 'X'):
            lexeme_chars.append(self._advance())
            lexeme_chars.append(self._advance())
            while self.position < self.length:
                next_char = self._peek()
                if next_char is not None and (next_char.isdigit() or next_char.lower() in ('a', 'b', 'c', 'd', 'e', 'f')):
                    lexeme_chars.append(self._advance())
                else:
                    break
            return Token(TokenType.LIT_INT, "".join(lexeme_chars), loc, start_pos, self.position)

        # Binary
        if char == '0' and self._peek(1) in ('b', 'B'):
            lexeme_chars.append(self._advance())
            lexeme_chars.append(self._advance())
            while self.position < self.length:
                next_char = self._peek()
                if next_char in ('0', '1'):
                    lexeme_chars.append(self._advance())
                else:
                    break
            return Token(TokenType.LIT_INT, "".join(lexeme_chars), loc, start_pos, self.position)

        # Decimals and floats
        is_float = False
        while self.position < self.length:
            next_char = self._peek()
            if next_char is None:
                break
            if next_char.isdigit():
                lexeme_chars.append(self._advance())
            elif next_char == '.' and not is_float:
                next_next = self._peek(1)
                if next_next is not None and next_next.isdigit():
                    is_float = True
                    lexeme_chars.append(self._advance())
                else:
                    break
            elif next_char in ('e', 'E'):
                is_float = True
                lexeme_chars.append(self._advance())
                exponent_next = self._peek()
                if exponent_next in ('+', '-'):
                    lexeme_chars.append(self._advance())
                while self.position < self.length:
                    dig = self._peek()
                    if dig is not None and dig.isdigit():
                        lexeme_chars.append(self._advance())
                    else:
                        break
                break
            else:
                break

        lexeme = "".join(lexeme_chars)
        token_type = TokenType.LIT_FLOAT if is_float else TokenType.LIT_INT
        return Token(token_type, lexeme, loc, start_pos, self.position)

    def _scan_number_starting_with_dot(self, start_pos: int, loc: SourceLocation) -> Token:
        lexeme_chars = [self._advance()]
        while self.position < self.length:
            next_char = self._peek()
            if next_char is not None and next_char.isdigit():
                lexeme_chars.append(self._advance())
            else:
                break
                
        next_char = self._peek()
        if next_char in ('e', 'E'):
            lexeme_chars.append(self._advance())
            exponent_next = self._peek()
            if exponent_next in ('+', '-'):
                lexeme_chars.append(self._advance())
            while self.position < self.length:
                dig = self._peek()
                if dig is not None and dig.isdigit():
                    lexeme_chars.append(self._advance())
                else:
                    break
        return Token(TokenType.LIT_FLOAT, "".join(lexeme_chars), loc, start_pos, self.position)

    def _scan_string(self, start_pos: int, loc: SourceLocation) -> Token:
        lexeme_chars = [self._advance()]
        terminated = False
        
        while self.position < self.length:
            char = self._peek()
            if char == '"':
                lexeme_chars.append(self._advance())
                terminated = True
                break
            elif char == '\\':
                lexeme_chars.append(self._advance())
                if self.position < self.length:
                    lexeme_chars.append(self._advance())
            elif char == '\n':
                break
            else:
                lexeme_chars.append(self._advance())

        lexeme = "".join(lexeme_chars)
        if not terminated:
            return Token(TokenType.INVALID, lexeme, loc, start_pos, self.position)
        return Token(TokenType.LIT_STRING, lexeme, loc, start_pos, self.position)

    def _scan_char(self, start_pos: int, loc: SourceLocation) -> Token:
        lexeme_chars = [self._advance()]
        terminated = False
        
        while self.position < self.length:
            char = self._peek()
            if char == "'":
                lexeme_chars.append(self._advance())
                terminated = True
                break
            elif char == '\\':
                lexeme_chars.append(self._advance())
                if self.position < self.length:
                    lexeme_chars.append(self._advance())
            else:
                lexeme_chars.append(self._advance())

        lexeme = "".join(lexeme_chars)
        if not terminated:
            return Token(TokenType.INVALID, lexeme, loc, start_pos, self.position)
            
        inner = lexeme[1:-1]
        is_valid = False
        if len(inner) == 1:
            is_valid = True
        elif len(inner) == 2 and inner[0] == '\\':
            if inner[1] in ('n', 't', 'r', '0', '\\', "'", '"'):
                is_valid = True
                
        if not is_valid:
            return Token(TokenType.INVALID, lexeme, loc, start_pos, self.position)
        return Token(TokenType.LIT_CHAR, lexeme, loc, start_pos, self.position)