# Save this file as tests/test_average_c.py

import pytest
from cc_analyzer.core.lexer import Lexer
from cc_analyzer.core.parser import Parser
from cc_analyzer.core.tokens import TokenType

# --- 72 Valid C Beginner Programs (CS101 level) ---
VALID_C_PROGRAMS = [
    # 1. Hello world block representation
    'void main() { printf("Hello, World!"); }',
    # 2. Arithmetic sum of integers
    'void main() { int a = 5; int b = 10; int sum = a + b; }',
    # 3. Floating point subtraction
    'void main() { float x = 5.5; float y = 1.2; float res = x - y; }',
    # 4. Multiplication with precision types
    'void main() { double a = 2.5; double b = 4.0; double prod = a * b; }',
    # 5. Basic division
    'void main() { int x = 10; int y = 2; int div = x / y; }',
    # 6. Modulo operation
    'void main() { int r = 10 % 3; }',
    # 7. Compound addition assignment
    'void main() { int x = 5; x += 10; }',
    # 8. Compound subtraction assignment
    'void main() { int y = 20; y -= 5; }',
    # 9. Compound multiplication assignment
    'void main() { int z = 3; z *= 4; }',
    # 10. Basic If conditional statement
    'void main() { int x = 5; if (x > 0) { printf("positive"); } }',
    # 11. If-else conditional structure
    'void main() { int x = -1; if (x >= 0) { printf("pos"); } else { printf("neg"); } }',
    # 12. Even or Odd check
    'void main() { int num = 7; if (num % 2 == 0) { printf("even"); } else { printf("odd"); } }',
    # 13. Largest among three numbers
    'void main() { int a = 5; int b = 10; int c = 3; int max = a; if (b > max) { max = b; } if (c > max) { max = c; } }',
    # 14. Leap year simplified check
    'void main() { int yr = 2024; if (yr % 4 == 0) { printf("leap"); } }',
    # 15. Value swapping of two variables
    'void main() { int a = 5; int b = 10; int temp = a; a = b; b = temp; }',
    # 16. Sequential increment inside while loop
    'void main() { int i = 0; while (i < 5) { i = i + 1; } }',
    # 17. Standard C89 loop structure
    'void main() { int i; for (i = 0; i < 5; i = i + 1) { printf("loop"); } }',
    # 18. Calculating sum of natural numbers
    'void main() { int sum = 0; int i; for (i = 1; i <= 10; i = i + 1) { sum = sum + i; } }',
    # 19. Factorial calculator function
    'int fact(int n) { int i; int res = 1; for (i = 1; i <= n; i = i + 1) { res = res * i; } return res; }',
    # 20. Fibonacci sequence initialization
    'void main() { int t1 = 0; int t2 = 1; int next = t1 + t2; }',
    # 21. Function with params and return
    'int add(int x, int y) { return x + y; }',
    # 22. Float average function with multiple parameters
    'float avg(float a, float b, float c) { return (a + b + c) / 3.0; }',
    # 23. Void return function
    'void greet() { printf("Hello!"); }',
    # 24. Math constant getter
    'double get_pi() { return 3.14159; }',
    # 25. Struct Node recursive definition
    'struct Node { int val; struct Node* next; };',
    # 26. Custom Point struct assignments
    'struct Point { int x; int y; }; void main() { struct Point p; p.x = 10; p.y = 20; }',
    # 27. Struct arrow pointer member access
    'struct Point { int x; }; void main() { struct Point p; struct Point* ptr = &p; ptr->x = 5; }',
    # 28. Declaring address-of pointer reference
    'void main() { int x = 10; int* ptr = &x; }',
    # 29. Pointer dereferencing
    'void main() { int x = 10; int* ptr = &x; int val = *ptr; }',
    # 30. Double dereferencing pointer chain
    'void main() { int x = 10; int* p = &x; int** pp = &p; int val = **pp; }',
    # 31. Array subscript indexing access
    'void main() { int* arr; int x = arr[0]; }',
    # 32. Assigning values to array index
    'void main() { int* arr; arr[1] = 42; }',
    # 33. Precedence rules mathematical evaluation (PEMDAS)
    'void main() { int res = 5 + 3 * 2 - 8 / 4; }',
    # 34. Custom operator precedence with parenthesis
    'void main() { int res = (5 + 3) * (2 - 8) / 4; }',
    # 35. Logical AND evaluation
    'void main() { int res = 1 && 0; }',
    # 36. Logical OR evaluation
    'void main() { int res = 1 || 0; }',
    # 37. Logical NOT evaluation
    'void main() { int res = !1; }',
    # 38. Complex boolean logical combinations
    'void main() { int res = (1 && 0) || !0; }',
    # 39. Relational checks
    'void main() { int res = 5 <= 10; }',
    # 40. Inequality checks
    'void main() { int res = 5 != 10; }',
    # 41. Equality checks
    'void main() { int res = 5 == 5; }',
    # 42. Deeply nested if-else conditional blocks
    'void main() { int x = 5; if (x > 0) { if (x < 10) { printf("pos single"); } } }',
    # 43. Celsius to Fahrenheit conversion formula
    'float c2f(float c) { return c * 9.0 / 5.0 + 32.0; }',
    # 44. Fahrenheit to Celsius conversion formula
    'float f2c(float f) { return (f - 32.0) * 5.0 / 9.0; }',
    # 45. Area of a circle math calculation
    'float area(float r) { return 3.14 * r * r; }',
    # 46. Area of a rectangle calculation
    'int area(int w, int h) { return w * h; }',
    # 47. Simple interest formula
    'float si(float p, float r, float t) { return p * r * t / 100.0; }',
    # 48. Squaring math formula
    'int sq(int x) { return x * x; }',
    # 49. Cubing math formula
    'int cb(int x) { return x * x * x; }',
    # 50. Char variables initialization
    "void main() { char c = 'z'; }",
    # 51. Variable floating point widening conversion
    'void main() { float f = 10; }',
    # 52. Mathematical absolute value function
    'int abs(int x) { if (x < 0) { return -x; } return x; }',
    # 53. Min function of two variables
    'int min(int x, int y) { if (x < y) { return x; } return y; }',
    # 54. Max function of two variables
    'int max(int x, int y) { if (x > y) { return x; } return y; }',
    # 55. Sequential isolated semicolon statements
    'void main() { ; ; }',
    # 56. Empty return statements
    'void f() { return; }',
    # 57. String literals containing esc characters
    'void main() { char* s = "hello\\nworld"; }',
    # 58. Struct nesting structure definition
    'struct A { int x; }; struct B { struct A a; };',
    # 59. Struct pointer assignment
    'struct Node { int val; }; void f() { struct Node n; struct Node* p = &n; }',
    # 60. Address-of parameter reference mutations
    'void update(int* p) { *p = 10; }',
    # 61. Compound unary pointer math evaluation
    'void main() { int x = 5; int* p = &x; int y = -*p; }',
    # 62. Deeply nested loops
    'void main() { int i; int j; for (i = 0; i < 3; i = i + 1) { for (j = 0; j < 3; j = j + 1) { printf("nested"); } } }',
    # 63. Multiple pointers declared sequentially
    'void main() { int* a; int* b; int* c; }',
    # 64. Double pointers definitions
    'void main() { int** ptr; }',
    # 65. Globally scoped variable definitions
    'int x = 5; float y = 10.0; void main() {}',
    # 66. Completely empty functions body
    'void f() {}',
    # 67. Parameters list of pointer types
    'void f(int* p, float* q) {}',
    # 68. Constant string variable assignments
    'void main() { char* s = "text"; }',
    # 69. Highly complex conditional logical evaluations
    'void main() { int res = (a == b) && (c != d) || (e < f); }',
    # 70. Inline nested assignment operations
    'void main() { int x; int y; x = y = 10; }',
    # 71. Empty for condition inside loop headers (Valid empty statements)
    'void main() { int i; for (i = 0;; i = i + 1) {} }',
    # 72. Semicolons empty statement inside if conditions (Valid empty statements)
    'void main() { if (x); {} }'
]

# --- 28 Invalid C Programs with common syntax/lexical issues ---
INVALID_C_PROGRAMS = [
    # 73. Semicolon omission in declaration block
    'void main() { int x = 5 }',
    # 74. Unclosed function body braces
    'void main() { int x = 5;',
    # 75. Mismatched parentheses in if conditionals
    'void main() { if (x > 0 { printf("err"); } }',
    # 76. Variable assignment of numerical lvalue targets
    'void main() { 5 = x; }',
    # 77. Invalid lexical character token inside assignments
    'void main() { int x = @; }',
    # 78. Unrecognized dollar sign lexical character
    'void main() { int x = $; }',
    # 79. Missing parameters parenthetical definition
    'void main { }',
    # 80. Mismatched square bracket indexing delimiter
    'void main() { int x = arr[0; }',
    # 81. Missing type name specifier during declarations
    'int main() { x y = 5; }',
    # 82. Dangling operator expression
    'void main() { int x = +; }',
    # 83. Complete omission of if conditional expressions
    'void main() { if () { } }',
    # 84. Complete omission of while conditional expressions
    'void main() { while () { } }',
    # 85. Mismatching comma delimiters inside for headers
    'void main() { int i; for (i = 0, i < 5, i = i + 1) {} }',
    # 86. Unterminated double-quoted string literals
    'void main() { char* s = "unclosed; }',
    # 87. Unterminated single-quoted char literals
    'void main() { char c = \'a; }',
    # 88. Trailing parameter delimiter commas
    'void f(int a,) {}',
    # 89. Trailing arguments list delimiter commas
    'void main() { f(a,); }',
    # 90. Malformed declaration statements
    'void main() { int = 5; }',
    # 91. Using language keyword as variable name
    'void main() { int return = 5; }',
    # 92. Missing struct opening braces
    'struct Point int x; };',
    # 93. Missing struct definition ending semicolons
    'struct Point { int x; }',
    # 94. Omission of function identifier
    'void (int x) {}',
    # 95. Parameters without identifier names definition
    'void f(int) {}',
    # 96. Unclosed nested block scope structures
    'void main() { { int x = 5; }',
    # 97. Multiple catastrophic syntax failures
    'void f( { int x = ; }',
    # 98. Empty pointer expressions
    'void main() { int *; }',
    # 99. Missing assignment values
    'void main() { x = ; }',
    # 100. Mismatched parenthesis inside variable expressions
    'void main() { int x = (5 + 3; }'
]


@pytest.mark.parametrize("source", VALID_C_PROGRAMS)
def test_valid_average_c_programs(source):
    """Verify that common, daily, first-year CS C programs parse successfully without syntactic errors."""
    lexer = Lexer(source)
    tokens = lexer.tokenize(keep_comments=False)
    parser = Parser(tokens)
    program = parser.parse()
    
    # Succeeded parse should not register any syntactic error in parser list
    assert len(parser.errors) == 0, f"Failed to parse valid C program:\n{source}\nErrors: {parser.errors}"


@pytest.mark.parametrize("source", INVALID_C_PROGRAMS)
def test_invalid_average_c_programs(source):
    """Verify that malformed or erroneous daily C programs are correctly flagged and blocked by the parser."""
    lexer = Lexer(source)
    tokens = lexer.tokenize(keep_comments=False)
    parser = Parser(tokens)
    program = parser.parse()
    
    # Erroneous programs must trigger either a lexical invalid token or a syntactic error
    has_lexer_error = any(t.type == TokenType.INVALID for t in tokens)
    has_parser_error = len(parser.errors) > 0
    
    assert has_lexer_error or has_parser_error, f"Erroneous program incorrectly parsed successfully:\n{source}"